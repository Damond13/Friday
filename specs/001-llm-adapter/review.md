# Code Review (Round 2): LLM 统一适配层 (001-llm-adapter)

**Reviewer**: 独立审核员 (只读模式)
**Date**: 2026-06-02
**Branch**: `001-llm-adapter`
**Previous Verdict**: CHANGES REQUIRED (8 个问题)
**Current Verdict**: **APPROVED**

---

## 审核总览

| 统计 | 数值 |
|------|------|
| 源文件 | 6 (含新增 types.py) |
| 测试文件 | 3 |
| 测试用例 | 23 (全部通过) |
| 通过项 | 12 |
| 不通过项 | 0 |
| 不适用 | 0 |

---

## 上一轮 8 个问题修复验证

### 问题 #1: json.loads 未捕获 JSONDecodeError

**状态**: 已修复

- `adapter.py` 第 155-158 行: `json.loads` 已被 `try/except json.JSONDecodeError` 包裹，捕获后抛出 `LLMResponseError`
- 测试覆盖: `test_chat_with_tool_calls` 间接验证了 tool_calls 解析路径
- 验证结果: 通过

### 问题 #2: chat_stream 迭代期间异常未捕获

**状态**: 已修复

- `adapter.py` 第 91 行: `chat_stream()` 整体被 `_wrap_llm_errors()` 上下文管理器包裹
- 生成器函数中使用 `with _wrap_llm_errors()` 后，迭代期间（`for chunk in stream`）抛出的异常会正确通过上下文管理器的 `__exit__` 被捕获并包装为自定义异常
- 经实际 Python 运行验证：生成器内部的异常确实会触发上下文管理器的异常处理路径
- 验证结果: 通过

### 问题 #3: adapter.py 超 200 行

**状态**: 已修复

- 新增 `types.py` 文件（24 行），包含 `TokenUsage`、`ToolCall`、`LLMResponse` 三个数据类
- `adapter.py` 从 238 行降至 167 行
- 验证结果: 通过

### 问题 #4: chat()/chat_stream() 超 30 行

**状态**: 已修复

- 提取 `_wrap_llm_errors()` 上下文管理器（第 31-45 行，14 行），统一处理异常包装
- `chat()`: 17 行（原 35 行）
- `chat_stream()`: 20 行（原 35 行）
- 所有函数均在 30 行限制内
- 验证结果: 通过

### 问题 #5: chat_stream() 缺返回类型注解

**状态**: 已修复

- `adapter.py` 第 4 行: 添加 `from collections.abc import Iterator` 导入
- `adapter.py` 第 89 行: `chat_stream()` 添加 `-> Iterator[str]` 返回类型注解
- 验证结果: 通过

### 问题 #6: get_client() 契约有 model 参数但实现无

**状态**: 已修复

- `contracts/llm-adapter.md` 第 7 行: `get_client` 签名已更新为 `get_client(provider: str | None = None) -> OpenAI`，不再包含 model 参数
- 实现与契约一致
- 验证结果: 通过

### 问题 #7: 契约用 list[Message] 但实现用 list[dict]

**状态**: 已修复

- `contracts/llm-adapter.md` 第 19 行: `chat()` 签名已更新为 `chat(messages: list[dict], ...)`，使用 `list[dict]` 而非 `list[Message]`
- `contracts/llm-adapter.md` 第 37 行: `chat_stream()` 同步更新
- `contracts/llm-adapter.md` 末尾新增注意事项说明使用 dict 的原因
- 实现与契约一致
- 验证结果: 通过

### 问题 #8: Message 数据类未实现

**状态**: 已修复

- `data-model.md` 已更新：将 `Message` 章节改为 "Message（dict 格式）"，说明直接使用 OpenAI SDK 的 dict 格式，不自定义数据类
- 文档明确列出了三种消息类型的 dict 示例
- 验证结果: 通过

---

## 逐项审核结果

### 1. Spec 合规

**结果**: 通过

逐条检查 FR-001 至 FR-009：

| 需求 | 状态 | 说明 |
|------|------|------|
| FR-001 统一 LLM 调用接口 | 通过 | `chat()` / `chat_stream()` 统一了调用方式 |
| FR-002 支持智谱和 DeepSeek | 通过 | config.py 定义了两个 provider 的 base_url，`PROVIDER_BASE_URLS` 映射 |
| FR-003 运行时切换模型 | 通过 | `switch_provider()` 实现，无需重启 |
| FR-004 上下文组装到 system prompt | 通过 | `build_system_prompt()` + `_inject_system_prompt()` 实现，支持用户记忆/知识/指令 |
| FR-005 工具调用定义 | 通过 | tools.py 定义了 shell_execute/file_read/file_write/knowledge_search 四个工具 |
| FR-006 失败时返回明确错误 | 通过 | `_wrap_llm_errors()` 上下文管理器统一包装异常，`json.loads` 也有独立 try/except |
| FR-007 对话历史传递 | 通过 | `chat()` 接受 messages 列表，支持多轮上下文 |
| FR-008 流式输出 | 通过 | `chat_stream()` 实现，返回 `Iterator[str]` |
| FR-009 配置文件管理 API Key | 通过 | config.py 从 `~/.friday/config.yaml` 读取，使用 `yaml.safe_load()` |

---

### 2. Constitution 合规

**结果**: 通过

| 原则 | 状态 | 说明 |
|------|------|------|
| I. 个人化优先 | 通过 | prompt 组装支持注入用户记忆和偏好 |
| II. 渐进式学习 | 通过 | MVP 先基础调用，后续迭代加更多功能 |
| III. 本地优先 | 通过 | 仅依赖 openai SDK，数据存本地 |
| IV. 安全可控 | 通过 | API Key 存配置文件，不硬编码 |
| V. 简洁实用 | 通过 | 基于 OpenAI SDK 统一适配，不过度设计 |
| 编码规范 | 通过 | 文件均不超 200 行，函数均不超 30 行，类型注解完整 |

---

### 3. 架构合规

**结果**: 通过

- `llm/` 只管 LLM 调用和 prompt 组装，符合 CLAUDE.md 定义
- config.py 负责配置加载，不在 llm/ 内部
- 模块间无循环依赖
- `adapter.py` 是 llm/ 对外的唯一入口，符合 adapter 层模式
- 新增 `types.py` 仅包含数据类定义，不引入额外耦合

---

### 4. 文件大小

**结果**: 通过

| 文件 | 行数 | 限制 | 状态 |
|------|------|------|------|
| src/friday/config.py | 88 | 200 | 通过 |
| src/friday/llm/adapter.py | 167 | 200 | 通过 |
| src/friday/llm/types.py | 24 | 200 | 通过 |
| src/friday/llm/prompts.py | 42 | 200 | 通过 |
| src/friday/llm/tools.py | 121 | 200 | 通过 |
| src/friday/llm/__init__.py | 36 | 200 | 通过 |

---

### 5. 函数大小

**结果**: 通过

| 函数 | 行数 | 限制 | 状态 |
|------|------|------|------|
| config.py / `_build_provider_config` | 9 | 30 | 通过 |
| config.py / `load_config` | 23 | 30 | 通过 |
| config.py / `get_llm_config` | 8 | 30 | 通过 |
| adapter.py / `_wrap_llm_errors` | 14 | 30 | 通过 |
| adapter.py / `get_client` | 15 | 30 | 通过 |
| adapter.py / `chat` | 17 | 30 | 通过 |
| adapter.py / `chat_stream` | 20 | 30 | 通过 |
| adapter.py / `switch_provider` | 7 | 30 | 通过 |
| adapter.py / `get_current_provider` | 4 | 30 | 通过 |
| adapter.py / `get_current_model` | 3 | 30 | 通过 |
| adapter.py / `_inject_system_prompt` | 11 | 30 | 通过 |
| adapter.py / `_get_active_config` | 5 | 30 | 通过 |
| adapter.py / `_parse_response` | 22 | 30 | 通过 |
| prompts.py / `build_system_prompt` | 23 | 30 | 通过 |
| tools.py / `get_tool_definitions` | 4 | 30 | 通过 |
| tools.py / `to_openai_format` | 10 | 30 | 通过 |

---

### 6. 类型注解

**结果**: 通过

| 函数 | 返回类型 | 参数注解 | 状态 |
|------|----------|----------|------|
| `get_client()` | `-> OpenAI` | 完整 | 通过 |
| `chat()` | `-> LLMResponse` | 完整 | 通过 |
| `chat_stream()` | `-> Iterator[str]` | 完整 | 通过 |
| `switch_provider()` | `-> None` | 完整 | 通过 |
| `get_current_provider()` | `-> str` | 完整 | 通过 |
| `get_current_model()` | `-> str` | 完整 | 通过 |
| `build_system_prompt()` | `-> str` | 完整 | 通过 |
| `get_tool_definitions()` | `-> list[dict]` | 完整 | 通过 |
| `load_config()` | `-> AppConfig` | 完整 | 通过 |
| `get_llm_config()` | `-> LLMConfig` | 完整 | 通过 |
| `_wrap_llm_errors()` | `contextmanager` 装饰器 | 无参数 | 通过 |
| `_inject_system_prompt()` | `-> list[dict]` | 完整 | 通过 |
| `_parse_response()` | `-> LLMResponse` | 完整 | 通过 |

---

### 7. Adapter 层

**结果**: 通过

- OpenAI SDK 的 `OpenAI`、`APIConnectionError`、`AuthenticationError`、`APIStatusError` 全部通过 `adapter.py` 封装
- 外部调用方只接触自定义异常 (`LLMError` 体系)，不接触 OpenAI 原生异常
- `yaml` 库通过 `config.py` 封装，不暴露给 llm/ 模块
- 外部模块使用 `friday.llm` 时只需 `from friday.llm import chat`，不直接依赖 OpenAI SDK

---

### 8. 测试覆盖

**结果**: 通过

23 个测试全部通过（0.27 秒完成）。覆盖情况：

| 模块 | 测试文件 | 用例数 | 覆盖情况 |
|------|----------|--------|----------|
| adapter.py | test_adapter.py | 11 | get_client, chat, chat_stream, switch_provider, 错误处理 |
| prompts.py | test_prompts.py | 6 | 空 context, 部分填充, 完整填充 |
| tools.py | test_tools.py | 6 | 格式验证, 名称验证, 必填字段, 默认值 |

核心路径均有测试覆盖。上一轮建议的补充项（`_inject_system_prompt` 直接测试、`chat_stream` 中途异常测试、`LLMResponseError` 直接测试、`load_config` 无配置时行为测试）仍未添加，但不阻塞通过。

---

### 9. 安全

**结果**: 通过

- `config.py` 使用 `yaml.safe_load()` 而非 `yaml.load()`，安全
- API Key 从配置文件读取，不硬编码在源码中
- 没有用户输入拼接到 Shell 命令的地方（工具定义只是 schema，实际执行在 executor/ 模块）
- `json.loads` 用于解析 LLM 返回的 tool call arguments，已被 try/except 包裹，无注入风险

---

### 10. 无过度工程化

**结果**: 通过

- 使用 OpenAI SDK 统一适配两个 provider，没有引入 litellm 等重量级库
- 数据类使用 `@dataclass`，没有用 Pydantic 等重型框架
- 模块级缓存 (`_client_cache`) 简单实用，没有搞复杂的连接池
- 全局状态 (`_current_provider`) 用简单变量，没有引入状态管理库
- 工具定义直接实例化 `ToolDefinition` 对象，没有搞插件系统
- 新增 `types.py` 仅 24 行，是最小必要的拆分，不过度

---

### 11. 接口契约

**结果**: 通过

对比 `contracts/llm-adapter.md` 和实际实现：

| 契约接口 | 实现匹配 | 说明 |
|----------|----------|------|
| `get_client(provider: str \| None = None) -> OpenAI` | 通过 | 签名一致，无多余 model 参数 |
| `chat(messages: list[dict], ...) -> LLMResponse` | 通过 | 类型一致，使用 list[dict] |
| `chat_stream(messages: list[dict], ...) -> Iterator[str]` | 通过 | 类型一致，返回注解完整 |
| `switch_provider(provider: str) -> None` | 通过 | 一致 |
| `get_current_provider() -> str` | 通过 | 一致 |
| `get_current_model() -> str` | 通过 | 一致 |
| `build_system_prompt(context) -> str` | 通过 | 一致 |
| `get_tool_definitions() -> list[dict]` | 通过 | 一致 |

---

### 12. 数据模型

**结果**: 通过

对比 `data-model.md` 和实际实现：

| 数据类 | data-model.md | 实现位置 | 匹配 |
|--------|---------------|----------|------|
| ProviderConfig | 4 字段 + max_tokens | config.py | 通过 |
| Message (dict 格式) | dict 说明（含示例） | 无需实现 | 通过 |
| ToolCall | 3 字段 | types.py | 通过 |
| ToolDefinition | 3 字段 + to_openai_format | tools.py | 通过 |
| LLMResponse | 3 字段 | types.py | 通过 |
| TokenUsage | 3 字段 | types.py | 通过 |

---

## 最终判定

### APPROVED

上一轮的 8 个问题全部已修复：

1. `json.loads` 已被 try/except 包裹 — 异常处理完整
2. `chat_stream` 迭代期间异常已被 `_wrap_llm_errors()` 上下文管理器覆盖 — 验证通过
3. adapter.py 从 238 行降至 167 行 — 新增 types.py（24 行）
4. `chat()` 从 35 行降至 17 行，`chat_stream()` 从 35 行降至 20 行 — 通过提取上下文管理器实现
5. `chat_stream()` 已添加 `-> Iterator[str]` 返回类型注解
6. 契约已更新，`get_client()` 不再包含 model 参数
7. 契约已更新，`messages` 参数使用 `list[dict]`，末尾有说明
8. 数据模型已更新，Message 章节改为 dict 格式说明

12 项审核清单全部通过，23 个测试全部通过。代码质量良好，可以合并。
