# 接口合约：执行器模块

**Branch**: `004-executor` | **Date**: 2026-06-02

## adapter.py — 统一执行接口

上层模块（cli/、llm/）通过 `adapter.py` 调用执行器，不直接引用内部模块。

### execute

执行一条命令，返回执行结果。

```python
async def execute(
    command: str,
    cwd: str | None = None,
    timeout: float | None = None,
    stream: bool = False,
) -> ExecutionResult:
    """执行命令

    Args:
        command: Shell 命令文本
        cwd: 工作目录，默认为当前目录
        timeout: 超时秒数，None 使用默认 30s
        stream: 是否流式输出

    Returns:
        ExecutionResult 包含退出码、输出、安全等级等信息

    Raises:
        CommandTimeoutError: 命令超时
        CommandDeniedError: 用户拒绝执行
    """
```

### execute_stream

流式执行命令，逐步产出输出。

```python
async def execute_stream(
    command: str,
    cwd: str | None = None,
    timeout: float | None = None,
) -> AsyncIterator[StreamChunk]:
    """流式执行命令，逐步产出输出块"""
```

### get_history

查询执行历史。

```python
def get_history(limit: int = 20, offset: int = 0) -> list[ExecutionRecord]:
    """获取最近的执行历史"""
```

### trust_command

将命令标记为信任。

```python
def trust_command(command: str) -> None:
    """将命令标记为信任（仅对 confirm 级别有效）"""
```

## 数据类

### ExecutionResult

```python
@dataclass
class ExecutionResult:
    command: str           # 执行的命令
    exit_code: int | None  # 退出码，None 表示超时/取消
    stdout: str            # 标准输出
    stderr: str            # 标准错误
    duration_ms: int       # 耗时毫秒
    safety_level: str      # safe / confirm / dangerous
    approved: bool         # 是否经过确认
    truncated: bool        # 输出是否被截断
```

### StreamChunk

```python
@dataclass
class StreamChunk:
    type: str    # "stdout" | "stderr" | "done"
    data: str    # 输出内容
```

### SafetyLevel

```python
class SafetyLevel(Enum):
    SAFE = "safe"              # 自动执行
    CONFIRM = "confirm"        # 首次确认
    DANGEROUS = "dangerous"    # 每次确认
```

## 异常类

```python
class ExecutorError(Exception): ...
class CommandTimeoutError(ExecutorError): ...   # 命令超时
class CommandDeniedError(ExecutorError): ...    # 用户拒绝
class CommandNotFoundError(ExecutorError): ...  # 命令不存在
```

## 确认回调

执行器需要用户确认时，通过回调函数询问上层。

```python
ConfirmCallback = Callable[[str, SafetyLevel], bool]
# 参数: (command, safety_level) → True=执行, False=拒绝
```
