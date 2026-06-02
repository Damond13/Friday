# Quick Start: LLM 统一适配层

## 前置条件

- Python 3.13+
- 智谱或 DeepSeek 的 API Key

## 1. 配置 API Key

首次使用时，编辑 `~/.friday/config.yaml`：

```yaml
llm:
  provider: zhipu
  providers:
    zhipu:
      api_key: "your-zhipu-api-key"
      model: "glm-4-flash"
      max_tokens: 4096
    deepseek:
      api_key: "your-deepseek-api-key"
      model: "deepseek-chat"
      max_tokens: 4096
```

## 2. 基础对话

```python
from friday.llm import chat

response = chat([{"role": "user", "content": "你好"}])
print(response.content)
```

## 3. 切换 Provider

```python
from friday.llm import switch_provider, get_current_provider

switch_provider("deepseek")
print(get_current_provider())  # "deepseek"
```

## 4. 覆盖模型

```python
from friday.llm import chat

# 不换 provider，临时用其他模型
response = chat(
    [{"role": "user", "content": "写一段快速排序"}],
    model="glm-5.1"
)
```

## 5. 工具调用

```python
from friday.llm import chat, get_tool_definitions

tools = get_tool_definitions()
response = chat(
    [{"role": "user", "content": "帮我看看当前目录有什么文件"}],
    tools=tools
)

if response.tool_calls:
    for tc in response.tool_calls:
        print(f"工具: {tc.name}, 参数: {tc.arguments}")
```

## 6. 流式输出

```python
from friday.llm import chat_stream

for token in chat_stream([{"role": "user", "content": "讲个故事"}]):
    print(token, end="", flush=True)
```

## 7. 错误处理

```python
from friday.llm import chat
from friday.llm.adapter import LLMConnectionError, LLMAuthError

try:
    response = chat([{"role": "user", "content": "你好"}])
except LLMConnectionError:
    print("网络连接失败，请检查网络")
except LLMAuthError:
    print("API Key 无效，请检查配置")
```
