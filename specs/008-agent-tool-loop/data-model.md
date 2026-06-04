# Data Model: Agent 工具调用循环

## 核心实体

### ToolCall

LLM 返回的工具调用请求。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | str | LLM 分配的调用 ID，用于结果回传匹配 |
| name | str | 工具名称（shell_execute / file_read / file_write / knowledge_search） |
| arguments | dict | 工具参数（LLM 生成的 JSON 对象） |

来源：已在 `llm/types.py` 中定义，无需新建。

### ToolResult

工具执行后的结果。

| 字段 | 类型 | 说明 |
|------|------|------|
| tool_call_id | str | 对应 ToolCall.id |
| success | bool | 执行是否成功 |
| output | str | 执行输出（stdout / 文件内容 / 搜索结果 / 错误信息） |

### ToolExecutor

工具执行函数的注册签名。

```python
# 类型别名
ToolExecutor = Callable[[dict], Awaitable[ToolResult]]
```

输入为 ToolCall.arguments，输出为 ToolResult。

### AgentLoopState

循环过程中的消息累积状态（非持久化）。

| 字段 | 类型 | 说明 |
|------|------|------|
| messages | list[dict] | 对话消息列表（含 system / user / assistant / tool 消息） |
| round_count | int | 当前已执行的工具调用轮次 |
| max_rounds | int | 最大允许轮次（默认 10） |

## 状态转换

```
START → call_llm
  call_llm → has_tool_calls?
    Yes → round < max_rounds?
      Yes → execute_tools → append_results → call_llm
      No  → STOP（超限提示）
    No  → stream_final_reply → STOP
```

## 消息格式

Agent 循环中使用的 OpenAI 消息角色：

| 角色 | 说明 |
|------|------|
| system | system prompt + context |
| user | 用户输入 |
| assistant | LLM 文本回复或 tool_calls |
| tool | 工具执行结果（role="tool"，tool_call_id 匹配） |
