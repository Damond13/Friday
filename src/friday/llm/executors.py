"""工具执行器注册表 — 工具名 → 执行函数的映射"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from pathlib import Path

from friday.llm.types import ToolResult

logger = logging.getLogger(__name__)

# 执行器类型：接收参数 dict，返回 ToolResult
ToolExecutor = Callable[[dict], Awaitable[ToolResult]]

# 确认回调类型：接收描述信息，返回是否允许
ConfirmCallback = Callable[[str], bool]

_EXECUTORS: dict[str, ToolExecutor] = {}
_confirm_callback: ConfirmCallback | None = None


def set_confirm_callback(callback: ConfirmCallback) -> None:
    """设置安全确认回调（CLI 层负责弹提示）"""
    global _confirm_callback
    _confirm_callback = callback


def get_executor(name: str) -> ToolExecutor | None:
    """获取指定工具的执行器"""
    return _EXECUTORS.get(name)


def get_all_executors() -> dict[str, ToolExecutor]:
    """获取所有已注册的执行器"""
    return _EXECUTORS.copy()


def _register(name: str, executor: ToolExecutor) -> None:
    """注册工具执行器"""
    _EXECUTORS[name] = executor


# ── shell_execute ──────────────────────────────────────

async def _exec_shell(arguments: dict) -> ToolResult:
    """执行 Shell 命令，复用 executor 模块的安全分级"""
    command = arguments.get("command", "")
    timeout = arguments.get("timeout", 30)
    if not command:
        return ToolResult(tool_call_id="", success=False, output="缺少 command 参数")
    try:
        from friday.executor import execute
        result = await execute(command, timeout=float(timeout))
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr] {result.stderr}"
        if result.exit_code != 0:
            output += f"\n[exit code: {result.exit_code}]"
        return ToolResult(tool_call_id="", success=result.exit_code == 0, output=output)
    except Exception as e:
        from friday.executor.errors import CommandDeniedError
        if isinstance(e, CommandDeniedError):
            return ToolResult(tool_call_id="", success=False, output=f"用户拒绝执行该命令")
        logger.warning(f"shell_execute 失败: {e}")
        return ToolResult(tool_call_id="", success=False, output=f"执行失败: {e}")


# ── file_read ──────────────────────────────────────────

async def _exec_file_read(arguments: dict) -> ToolResult:
    """读取文件内容"""
    path = arguments.get("path", "")
    if not path:
        return ToolResult(tool_call_id="", success=False, output="缺少 path 参数")
    try:
        p = Path(path).expanduser()
        if not p.exists():
            return ToolResult(tool_call_id="", success=False, output=f"文件不存在: {path}")
        if p.is_dir():
            return ToolResult(tool_call_id="", success=False, output=f"路径是目录，不是文件: {path}")
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        offset = arguments.get("offset", 0)
        limit = arguments.get("limit")
        selected = lines[offset:]
        if limit:
            selected = selected[:limit]
        content = "\n".join(selected)
        return ToolResult(tool_call_id="", success=True, output=content)
    except Exception as e:
        return ToolResult(tool_call_id="", success=False, output=f"读取失败: {e}")


# ── file_write ─────────────────────────────────────────

async def _exec_file_write(arguments: dict) -> ToolResult:
    """写入文件，覆写已存在文件时需确认"""
    path = arguments.get("path", "")
    content = arguments.get("content", "")
    if not path:
        return ToolResult(tool_call_id="", success=False, output="缺少 path 参数")
    try:
        p = Path(path).expanduser()
        if p.exists() and _confirm_callback:
            if not _confirm_callback(f"覆写文件: {path}"):
                return ToolResult(tool_call_id="", success=False, output=f"用户拒绝覆写: {path}")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return ToolResult(tool_call_id="", success=True, output=f"已写入 {p}")
    except Exception as e:
        return ToolResult(tool_call_id="", success=False, output=f"写入失败: {e}")


# ── knowledge_search ───────────────────────────────────

async def _exec_knowledge_search(arguments: dict) -> ToolResult:
    """搜索知识库"""
    query = arguments.get("query", "")
    limit = arguments.get("limit", 5)
    if not query:
        return ToolResult(tool_call_id="", success=False, output="缺少 query 参数")
    try:
        from friday.knowledge.adapter import search as kb_search
        results = kb_search(query, mode="auto", limit=limit)
        if not results:
            return ToolResult(tool_call_id="", success=True, output="未找到相关知识")
        parts: list[str] = []
        for r in results:
            parts.append(f"## {r.title}\n{r.snippet}\n")
        return ToolResult(tool_call_id="", success=True, output="\n".join(parts))
    except Exception as e:
        return ToolResult(tool_call_id="", success=False, output=f"搜索失败: {e}")


# ── 注册所有执行器 ────────────────────────────────────────

_register("shell_execute", _exec_shell)
_register("file_read", _exec_file_read)
_register("file_write", _exec_file_write)
_register("knowledge_search", _exec_knowledge_search)
