"""执行器模块 — 公共 API 导出"""

from friday.executor.adapter import (
    execute,
    execute_stream,
    get_history_records,
    set_confirm_callback,
    trust_command,
)
from friday.executor.errors import (
    CommandDeniedError,
    CommandNotFoundError,
    CommandTimeoutError,
    ExecutorError,
)
from friday.executor.history import ExecutionRecord
from friday.executor.runner import ExecutionResult, StreamChunk
from friday.executor.safety import SafetyLevel

# 兼容旧引用
get_history = get_history_records

__all__ = [
    "execute",
    "execute_stream",
    "get_history",
    "get_history_records",
    "set_confirm_callback",
    "trust_command",
    "ExecutionResult",
    "StreamChunk",
    "ExecutionRecord",
    "SafetyLevel",
    "ExecutorError",
    "CommandTimeoutError",
    "CommandDeniedError",
    "CommandNotFoundError",
]
