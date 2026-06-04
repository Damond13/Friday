"""Agent 循环单元测试 — mock LLM 和工具执行器"""

import json
from unittest.mock import MagicMock, patch

import pytest

from friday.llm.agent import run_agent_loop
from friday.llm.prompts import PromptContext
from friday.llm.types import AgentResult, LLMResponse, ToolCall, ToolResult


def _make_tool_call(name: str, args: dict, call_id: str = "tc_1") -> ToolCall:
    return ToolCall(id=call_id, name=name, arguments=args)


def _text_response(text: str) -> LLMResponse:
    return LLMResponse(content=text, tool_calls=[])


def _tool_call_response(*calls: ToolCall) -> LLMResponse:
    return LLMResponse(content="", tool_calls=list(calls))


# ── 普通对话不触发工具 ──────────────────────────────────

@patch("friday.llm.agent.chat")
def test_plain_text_no_tools(mock_chat: MagicMock):
    mock_chat.return_value = _text_response("你好！我是 Friday。")
    messages = [{"role": "user", "content": "你好"}]
    result = run_agent_loop(messages)

    assert isinstance(result, AgentResult)
    assert result.reply == "你好！我是 Friday。"
    assert result.tool_calls_count == 0
    assert mock_chat.call_count == 1


# ── 单个 tool_call 路由执行 ──────────────────────────────

async def _async_return(value):
    """异步包装，用于 mock 异步执行器"""
    return value


@patch("friday.llm.agent.chat")
def test_single_tool_call(mock_chat: MagicMock):
    tc = _make_tool_call("file_read", {"path": "/tmp/test.txt"})
    mock_chat.side_effect = [
        _tool_call_response(tc),
        _text_response("文件内容是 hello world"),
    ]
    result_val = ToolResult(tool_call_id="tc_1", success=True, output="hello world")
    mock_executor = MagicMock(return_value=_async_return(result_val))
    with patch("friday.llm.agent.get_executor", return_value=mock_executor):
        result = run_agent_loop([{"role": "user", "content": "读文件"}])

    assert result.reply == "文件内容是 hello world"
    assert result.tool_calls_count == 1
    mock_executor.assert_called_once_with({"path": "/tmp/test.txt"})


# ── 多个 tool_call 依次执行 ──────────────────────────────

@patch("friday.llm.agent.chat")
def test_multiple_tool_calls(mock_chat: MagicMock):
    tc1 = _make_tool_call("file_read", {"path": "a.txt"}, "tc_1")
    tc2 = _make_tool_call("knowledge_search", {"query": "test"}, "tc_2")
    mock_chat.side_effect = [
        _tool_call_response(tc1, tc2),
        _text_response("综合结果是..."),
    ]
    exec_outputs = [
        _async_return(ToolResult(tool_call_id="tc_1", success=True, output="content_a")),
        _async_return(ToolResult(tool_call_id="tc_2", success=True, output="search_result")),
    ]
    mock_executor = MagicMock(side_effect=exec_outputs)
    with patch("friday.llm.agent.get_executor", return_value=mock_executor):
        result = run_agent_loop([{"role": "user", "content": "读文件并搜索"}])

    assert result.reply == "综合结果是..."
    assert result.tool_calls_count == 2
    assert mock_executor.call_count == 2


# ── 工具执行错误回传 ────────────────────────────────────

@patch("friday.llm.agent.chat")
def test_tool_error_feed_back(mock_chat: MagicMock):
    tc = _make_tool_call("shell_execute", {"command": "bad_cmd"}, "tc_1")
    mock_chat.side_effect = [
        _tool_call_response(tc),
        _text_response("命令执行失败了。"),
    ]
    mock_executor = MagicMock(return_value=_async_return(ToolResult(
        tool_call_id="tc_1", success=False, output="命令未找到",
    )))
    with patch("friday.llm.agent.get_executor", return_value=mock_executor):
        result = run_agent_loop([{"role": "user", "content": "执行命令"}])

    assert result.tool_calls_count == 1
    tool_msg = [m for m in result.messages if m.get("role") == "tool"]
    assert len(tool_msg) == 1
    assert "命令未找到" in tool_msg[0]["content"]


# ── 超限停止 ───────────────────────────────────────────

@patch("friday.llm.agent.chat")
def test_max_rounds_stop(mock_chat: MagicMock):
    tc = _make_tool_call("file_read", {"path": "loop.txt"}, "tc_loop")
    mock_chat.return_value = _tool_call_response(tc)
    result_val = ToolResult(tool_call_id="tc_loop", success=True, output="data")
    mock_executor = MagicMock(side_effect=lambda args: _async_return(result_val))
    with patch("friday.llm.agent.get_executor", return_value=mock_executor):
        with patch("friday.llm.agent.MAX_ROUNDS", 3):
            result = run_agent_loop([{"role": "user", "content": "loop"}])

    assert "最大轮次" in result.reply
    assert result.tool_calls_count == 3


# ── 未知工具处理 ────────────────────────────────────────

@patch("friday.llm.agent.chat")
def test_unknown_tool(mock_chat: MagicMock):
    tc = _make_tool_call("nonexistent_tool", {"x": 1}, "tc_1")
    mock_chat.side_effect = [
        _tool_call_response(tc),
        _text_response("工具不存在。"),
    ]
    with patch("friday.llm.agent.get_executor", return_value=None):
        result = run_agent_loop([{"role": "user", "content": "test"}])

    tool_msg = [m for m in result.messages if m.get("role") == "tool"]
    assert "未知工具" in tool_msg[0]["content"]


# ── 回调函数被正确调用 ──────────────────────────────────

@patch("friday.llm.agent.chat")
def test_callbacks_called(mock_chat: MagicMock):
    tc = _make_tool_call("file_read", {"path": "test.txt"}, "tc_1")
    mock_chat.side_effect = [
        _tool_call_response(tc),
        _text_response("done"),
    ]
    mock_executor = MagicMock(return_value=_async_return(ToolResult(
        tool_call_id="tc_1", success=True, output="ok",
    )))
    on_tc = MagicMock()
    on_tr = MagicMock()
    with patch("friday.llm.agent.get_executor", return_value=mock_executor):
        run_agent_loop(
            [{"role": "user", "content": "test"}],
            on_tool_call=on_tc,
            on_tool_result=on_tr,
        )

    on_tc.assert_called_once_with("file_read", {"path": "test.txt"})
    on_tr.assert_called_once_with(True, "ok")
