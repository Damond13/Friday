"""统一执行接口 — 上层模块的唯一入口"""

from collections.abc import AsyncIterator, Callable

from friday.executor.errors import (
    CommandDeniedError,
    CommandNotFoundError,
    CommandTimeoutError,
    ExecutorError,
)
from friday.executor.history import ExecutionRecord, get_history
from friday.executor.runner import ExecutionResult, StreamChunk, run, run_stream
from friday.executor.safety import SafetyLevel, add_trusted, classify

ConfirmCallback = Callable[[str, SafetyLevel], bool]

_confirm_callback: ConfirmCallback | None = None


def set_confirm_callback(callback: ConfirmCallback) -> None:
    """设置用户确认回调（CLI 层负责弹提示）"""
    global _confirm_callback
    _confirm_callback = callback


def trust_command(command: str) -> None:
    """将命令标记为信任"""
    add_trusted(command)


async def execute(
    command: str,
    cwd: str | None = None,
    timeout: float | None = None,
) -> ExecutionResult:
    """执行命令，串联安全检查 → 确认 → 执行 → 输出处理 → 历史记录"""
    from friday.executor.output import format_output, format_error
    from friday.executor.history import save_record

    level, approved = _check_and_confirm(command)
    result = await run(command, cwd=cwd, timeout=timeout)
    result.safety_level = level
    result.approved = approved

    _format_result(result)
    _post_execute(command, level, approved, result, cwd)
    return result


async def execute_stream(
    command: str,
    cwd: str | None = None,
    timeout: float | None = None,
) -> AsyncIterator[StreamChunk]:
    """流式执行命令（含安全确认、信任记忆、历史记录）"""
    from friday.executor.history import save_record
    from friday.executor.runner import ExecutionResult as ER

    level, approved = _check_and_confirm(command)
    started_at_ms = _now_ms()
    exit_code: int | None = None
    chunks: list[str] = []

    async for chunk in run_stream(command, cwd=cwd, timeout=timeout):
        if chunk.type == "done":
            exit_code = int(chunk.data)
        else:
            chunks.append(chunk.data)
        yield chunk

    _post_execute(command, level, approved, ER(
        command=command, exit_code=exit_code,
        stdout="".join(chunks), duration_ms=_now_ms() - started_at_ms,
        safety_level=level, approved=approved,
    ), cwd)


def get_history_records(limit: int = 20, offset: int = 0) -> list[ExecutionRecord]:
    """查询执行历史"""
    return get_history(limit=limit, offset=offset)


def _check_and_confirm(command: str) -> tuple[SafetyLevel, bool]:
    """安全分类 + 确认"""
    level = classify(command)
    if level == SafetyLevel.SAFE:
        return level, False
    approved = _ask_confirm(command, level)
    if not approved:
        raise CommandDeniedError(f"用户拒绝执行: {command}")
    return level, approved


def _ask_confirm(command: str, level: SafetyLevel) -> bool:
    """调用确认回调，危险命令无回调时拒绝"""
    if _confirm_callback is None:
        if level == SafetyLevel.DANGEROUS:
            return False
        return True
    return _confirm_callback(command, level)


def _format_result(result: ExecutionResult) -> None:
    """格式化输出"""
    from friday.executor.output import format_output, format_error
    if result.exit_code == 0:
        result.stdout = format_output(result.stdout)
    else:
        result.stderr = format_error(result.exit_code, result.stderr)


def _post_execute(
    command: str, level: SafetyLevel, approved: bool,
    result: ExecutionResult, cwd: str | None,
) -> None:
    """执行后处理：信任记忆 + 历史记录"""
    if level == SafetyLevel.CONFIRM and approved:
        add_trusted(command.strip().split()[0])
    from friday.executor.history import save_record
    try:
        save_record(result, cwd=cwd)
    except Exception:
        pass


def _now_ms() -> int:
    """当前时间戳（毫秒）"""
    import time
    return int(time.monotonic() * 1000)
