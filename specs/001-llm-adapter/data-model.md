# Data Model: LLM 统一适配层

## ProviderConfig

提供商标识和连接配置，从 `~/.friday/config.yaml` 读取。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | str | 是 | "zhipu" / "deepseek" |
| base_url | str | 是 | API endpoint |
| api_key | str | 是 | 从配置文件读取，不硬编码 |
| model | str | 是 | 默认模型名 |
| max_tokens | int | 否 | 单次回复最大 token，默认 4096 |

## Message（dict 格式）

对话消息直接使用 OpenAI SDK 的 dict 格式，不自定义数据类，避免不必要的序列化转换。

```python
# 标准消息
{"role": "user", "content": "你好"}

# 带工具调用的助手消息（由 LLM 返回，在 ToolCall 中解析）
{"role": "assistant", "content": null, "tool_calls": [...]}

# 工具结果消息
{"role": "tool", "tool_call_id": "call_123", "content": "..."}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| role | str | 是 | "system" / "user" / "assistant" / "tool" |
| content | str | 是 | 消息内容 |
| tool_calls | list | 否 | LLM 返回的工具调用（仅 assistant 角色，在 ToolCall 数据类中解析） |
| tool_call_id | str | 否 | 工具调用结果 ID（仅 tool 角色） |

## ToolCall

LLM 发起的工具调用请求。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | str | 调用唯一标识 |
| name | str | 工具名称 |
| arguments | dict | 调用参数 |

## ToolDefinition

工具定义，遵循 OpenAI function calling schema。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | str | 是 | 工具名称（如 "shell_execute"） |
| description | str | 是 | 工具描述（给 LLM 理解用） |
| parameters | dict | 是 | JSON Schema 格式的参数定义 |

## LLMResponse

LLM 调用的统一返回结果。

| 字段 | 类型 | 说明 |
|------|------|------|
| content | str | 文本回复（可能为空，当有 tool_calls 时） |
| tool_calls | list[ToolCall] | 工具调用请求（可能为空） |
| usage | TokenUsage | token 用量统计 |

## TokenUsage

Token 消耗统计。

| 字段 | 类型 | 说明 |
|------|------|------|
| prompt_tokens | int | 输入 token 数 |
| completion_tokens | int | 输出 token 数 |
| total_tokens | int | 总 token 数 |

## 数据关系

```
ProviderConfig → adapter.py 使用 → 创建 OpenAI client
ToolDefinition[] → tools.py 定义 → 传入 LLM 调用
Message[] → prompts.py 组装 → 传入 LLM 调用
LLM 调用 → 返回 → LLMResponse (content + tool_calls)
```
