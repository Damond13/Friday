# 工具执行器注册契约

每个工具执行器必须遵循以下接口：

## 输入

```python
async def executor(arguments: dict) -> ToolResult
```

`arguments` 字段由 LLM 根据工具定义（`tools.py`）生成。

## 输出

```python
@dataclass
class ToolResult:
    tool_call_id: str   # 匹配 ToolCall.id
    success: bool       # 执行是否成功
    output: str         # 输出内容或错误信息
```

## 已注册工具

### shell_execute

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| command | str | 是 | 要执行的 Shell 命令 |
| timeout | int | 否 | 超时秒数，默认 30 |

安全策略：复用 `executor/adapter.py` 的 `execute()` 流程（classify → confirm → run → history）。
REPL 层需通过 `set_confirm_callback()` 注册确认回调。

### file_read

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| path | str | 是 | 文件路径 |
| offset | int | 否 | 起始行号（从 0 开始） |
| limit | int | 否 | 最大读取行数 |

安全策略：无特殊限制，直接读取。

### file_write

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| path | str | 是 | 文件路径 |
| content | str | 是 | 要写入的内容 |

安全策略：目标文件已存在时，需要用户确认后才能覆写。

### knowledge_search

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | str | 是 | 搜索查询 |
| limit | int | 否 | 返回结果数量，默认 5 |

安全策略：只读操作，无限制。
