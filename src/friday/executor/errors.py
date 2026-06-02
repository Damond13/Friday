"""执行器异常层级"""


class ExecutorError(Exception):
    """执行器异常基类"""

class CommandTimeoutError(ExecutorError):
    """命令执行超时"""

class CommandDeniedError(ExecutorError):
    """用户拒绝执行"""

class CommandNotFoundError(ExecutorError):
    """命令不存在"""
