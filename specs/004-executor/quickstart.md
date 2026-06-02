# 快速上手：执行器模块

**Branch**: `004-executor` | **Date**: 2026-06-02

## 集成场景

### 场景 1：CLI 交互壳调用执行器

```python
from friday.executor.adapter import execute, set_confirm_callback

# 设置确认回调（CLI 层负责弹确认提示）
set_confirm_callback(cli_confirm_handler)

# 执行安全命令（自动执行）
result = await execute("ls -la")
print(result.stdout)

# 执行危险命令（自动弹确认）
result = await execute("rm temp.log")
# → cli_confirm_handler 被调用，用户确认后执行
```

### 场景 2：LLM 工具调用触发执行

```python
from friday.executor.adapter import execute, ExecutionResult

# LLM 返回 tool_call，执行器负责执行
async def handle_tool_call(tool_name: str, args: dict) -> ExecutionResult:
    if tool_name == "run_command":
        return await execute(args["command"], timeout=30)
    raise ValueError(f"未知工具: {tool_name}")
```

### 场景 3：查看执行历史

```python
from friday.executor.adapter import get_history

records = get_history(limit=10)
for r in records:
    print(f"[{r.safety_level}] {r.command} → exit={r.exit_code} ({r.duration_ms}ms)")
```

### 场景 4：流式输出

```python
from friday.executor.adapter import execute_stream

async for chunk in execute_stream("ping -c 5 google.com"):
    if chunk.type == "stdout":
        print(chunk.data, end="")
    elif chunk.type == "done":
        print("\n完成")
```

## 测试场景

### 测试 1：安全命令自动执行

```python
async def test_safe_command():
    result = await execute("echo hello")
    assert result.exit_code == 0
    assert result.stdout.strip() == "hello"
    assert result.safety_level == "safe"
    assert result.approved is False
```

### 测试 2：危险命令需要确认

```python
async def test_dangerous_command_needs_confirm():
    set_confirm_callback(lambda cmd, level: True)  # 自动确认
    result = await execute("rm -rf /tmp/test")
    assert result.safety_level == "dangerous"
    assert result.approved is True
```

### 测试 3：超时处理

```python
async def test_timeout():
    with pytest.raises(CommandTimeoutError):
        await execute("sleep 60", timeout=1)
```

### 测试 4：命令不存在

```python
async def test_command_not_found():
    result = await execute("nonexistent_command_xyz")
    assert result.exit_code != 0
    assert "not found" in result.stderr.lower() or result.exit_code == 127
```

### 测试 5：历史记录

```python
async def test_history():
    await execute("echo test1")
    await execute("echo test2")
    records = get_history(limit=2)
    assert len(records) == 2
    assert "echo test2" in records[0].command
```
