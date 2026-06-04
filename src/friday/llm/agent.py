"""Agent 循环控制器 — LLM 调用 → tool_call 检测 → 工具执行 → 结果回传"""

import asyncio
import json
import logging
from collections.abc import Callable

from friday.llm.adapter import chat
from friday.llm.executors import get_executor
from friday.llm.prompts import PromptContext
from friday.llm.tools import get_tool_definitions
from friday.llm.types import AgentResult, ToolCall, ToolResult

logger = logging.getLogger(__name__)

MAX_ROUNDS = 10

OnToolCall = Callable[[str, dict], None]
OnToolResult = Callable[[bool, str], None]


def run_agent_loop(
    messages: list[dict],
    context: PromptContext | None = None,
    on_tool_call: OnToolCall | None = None,
    on_tool_result: OnToolResult | None = None,
) -> AgentResult:
    """执行 Agent 循环：LLM 调用 → tool_call 检测 → 工具执行 → 结果回传"""
    tools = get_tool_definitions()
    working = list(messages)
    total = 0

    for round_num in range(MAX_ROUNDS):
        response = chat(working, tools=tools, context=context)
        if round_num == 0:
            context = None

        if not response.tool_calls:
            return AgentResult(reply=response.content, messages=working, tool_calls_count=total)

        working.append(_build_tool_calls_msg(response.tool_calls, response.content))
        total += _process_tool_calls(response.tool_calls, working, on_tool_call, on_tool_result)

    logger.warning(f"Agent 循环达到最大轮次 {MAX_ROUNDS}")
    return AgentResult(
        reply=f"工具调用已达最大轮次（{MAX_ROUNDS} 次），操作未完全完成。",
        messages=working, tool_calls_count=total,
    )


def _build_tool_calls_msg(tool_calls: list[ToolCall], content: str) -> dict:
    """构建 assistant 的 tool_calls 消息"""
    return {
        "role": "assistant",
        "content": content or "",
        "tool_calls": [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.name, "arguments": json.dumps(tc.arguments, ensure_ascii=False)},
            }
            for tc in tool_calls
        ],
    }


def _process_tool_calls(
    tool_calls: list[ToolCall],
    messages: list[dict],
    on_call: OnToolCall | None,
    on_result: OnToolResult | None,
) -> int:
    """逐个执行工具调用并追加结果，返回执行次数"""
    count = 0
    for tc in tool_calls:
        if on_call:
            on_call(tc.name, tc.arguments)
        result = _execute_tool(tc.id, tc.name, tc.arguments)
        count += 1
        if on_result:
            on_result(result.success, result.output)
        messages.append({"role": "tool", "tool_call_id": tc.id, "content": result.output})
    return count


def _execute_tool(tool_call_id: str, name: str, arguments: dict) -> ToolResult:
    """路由到对应执行器并执行"""
    executor = get_executor(name)
    if executor is None:
        return ToolResult(tool_call_id=tool_call_id, success=False, output=f"未知工具: {name}")
    try:
        result = asyncio.run(executor(arguments))
        result.tool_call_id = tool_call_id
        return result
    except RuntimeError:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, executor(arguments))
            result = future.result(timeout=60)
            result.tool_call_id = tool_call_id
            return result
    except Exception as e:
        logger.error(f"工具 {name} 执行异常: {e}")
        return ToolResult(tool_call_id=tool_call_id, success=False, output=f"工具执行异常: {e}")
