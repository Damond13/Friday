# LLM Adapter 接口契约

## 模块: `friday.llm`

### 公开接口

#### `get_client(provider: str | None = None) -> OpenAI`

根据 provider 名称返回配置好的 OpenAI client。

**参数**:
- `provider` (str | None): "zhipu" / "deepseek"，为 None 时使用当前 provider

**返回**: 配置好 base_url 和 api_key 的 OpenAI client 实例

---

#### `chat(messages: list[dict], tools: list[dict] | None = None, model: str | None = None, context: PromptContext | None = None) -> LLMResponse`

发送对话请求，返回统一格式的响应。

**参数**:
- `messages` (list[dict]): 对话消息列表（OpenAI 消息格式 dict）
- `tools` (list[dict] | None): 可用工具定义（OpenAI function calling 格式）
- `model` (str | None): 覆盖默认模型
- `context` (PromptContext | None): 上下文信息，自动注入 system prompt

**返回**: LLMResponse（文本内容 + 可选工具调用）

**异常**:
- `LLMConnectionError`: 网络不可达或 API 超时
- `LLMAuthError`: API Key 无效或未配置
- `LLMResponseError`: 返回格式异常

---

#### `chat_stream(messages: list[dict], tools: list[dict] | None = None, model: str | None = None, context: PromptContext | None = None) -> Iterator[str]`

流式发送对话请求，逐 token 返回文本。

**参数**: 同 `chat()`

**返回**: token 字符串的迭代器

---

#### `switch_provider(provider: str) -> None`

运行时切换 LLM provider，无需重启。切换后使用新 provider 的默认模型。

**参数**:
- `provider` (str): 目标 provider 名称

---

#### `get_current_provider() -> str`

获取当前使用的 provider 名称。

**返回**: "zhipu" / "deepseek"

---

#### `get_current_model() -> str`

获取当前使用的模型名称。

**返回**: 模型标识字符串（如 "glm-4-flash"）

---

#### `build_system_prompt(context: PromptContext) -> str`

组装完整 system prompt。

**参数**:
- `context` (PromptContext): 包含用户记忆、知识、指令的上下文对象

**返回**: 完整的 system prompt 字符串

---

#### `get_tool_definitions() -> list[dict]`

返回所有可用工具的 function calling 定义（OpenAI 格式）。

**返回**: 工具定义列表，可直接传入 `chat()` 的 `tools` 参数

> **注意**: `chat()` 和 `chat_stream()` 的 `messages` 参数使用 `list[dict]`（OpenAI SDK 原生消息格式），而非自定义 `Message` 类。这避免了不必要的序列化转换层。

---

### PromptContext

| 字段 | 类型 | 说明 |
|------|------|------|
| user_memories | list[str] | 用户偏好和习惯 |
| knowledge | list[str] | 检索到的知识片段 |
| instructions | list[str] | 已学习的指令定义 |

### 错误处理

所有 LLM 调用错误统一包装为以下异常，不暴露底层 SDK 异常：

| 异常 | 触发条件 | 用户看到的提示 |
|------|----------|----------------|
| LLMConnectionError | 网络超时、服务不可达 | "网络连接失败，请检查网络" |
| LLMAuthError | API Key 无效 | "API Key 无效，请检查配置" |
| LLMResponseError | 返回格式异常 | "AI 回复异常，请重试" |
