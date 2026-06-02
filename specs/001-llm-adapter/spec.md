# Feature Specification: LLM 统一适配层

**Feature Branch**: `001-llm-adapter`

**Created**: 2026-06-01

**Status**: Draft

**Input**: User description: "LLM 调用层（llm/）— Friday 的 LLM 统一适配层，支持智谱 API 和 DeepSeek API 双模型切换，包含 adapter 模式封装、system prompt 组装（项目记忆 + 动态记忆 + 指令列表 + 知识上下文）、工具调用定义（Shell 执行/文件读写/知识库检索）。是所有模块的决策中枢。"

## User Scenarios & Testing

### User Story 1 - 基础对话 (Priority: P1)

用户在 CLI 中输入自然语言，Friday 通过 LLM 生成回复并显示。这是最基础的用户旅程——没有 LLM 调用就没有任何功能。

**Why this priority**: LLM 调用是一切功能的基础。没有它，Friday 无法响应任何输入。

**Independent Test**: 可以通过发送一条消息并验证收到非空回复来独立测试。

**Acceptance Scenarios**:

1. **Given** LLM 服务可用，**When** 用户发送"你好"，**Then** Friday 返回非空文本回复
2. **Given** LLM 服务不可用，**When** 用户发送消息，**Then** Friday 返回明确的错误提示而非崩溃

---

### User Story 2 - 模型切换 (Priority: P2)

用户在不同场景下需要使用不同模型（智谱用于日常对话，DeepSeek 用于代码相关任务），通过一条命令即可切换。

**Why this priority**: 双模型支持是架构核心差异，但不阻塞基础对话功能。

**Independent Test**: 切换模型后发送消息，验证请求发送到了正确的模型。

**Acceptance Scenarios**:

1. **Given** 当前使用智谱模型，**When** 用户执行模型切换命令，**Then** 后续对话使用新模型，用户收到切换确认
2. **Given** 当前使用智谱模型，**When** 用户查看当前模型，**Then** 显示"智谱"

---

### User Story 3 - 上下文组装 (Priority: P3)

用户与 Friday 对话时，LLM 自动获得用户的个人上下文信息（偏好、习惯、已学知识、已定义指令），无需手动重复说明。Friday 不依赖任何项目，是跨项目通用的个人助手。

**Why this priority**: 上下文组装让 Friday 真正具备个人化能力，但需要其他模块（memory/knowledge/instruction）先提供数据。

**Independent Test**: 模拟传入记忆和知识数据，验证 LLM 收到的完整 prompt 包含这些上下文。

**Acceptance Scenarios**:

1. **Given** 用户有存储的偏好"我喜欢简洁的回答"，**When** 用户发起对话，**Then** LLM 收到的 system prompt 中包含该偏好
2. **Given** 用户之前教过 Friday 一个指令，**When** 用户触发该指令关键词，**Then** LLM 的上下文中包含该指令定义

---

### User Story 4 - 工具调用 (Priority: P4)

LLM 判断需要执行操作时（如搜索知识库、读取文件），通过工具调用机制触发相应动作并返回结果。

**Why this priority**: 工具调用让 Friday 从"聊天机器人"升级为"能做事的助手"，但依赖执行器模块配合。

**Independent Test**: 构造 LLM 返回工具调用指令，验证能正确解析并分发。

**Acceptance Scenarios**:

1. **Given** LLM 判断需要执行命令，**When** LLM 返回工具调用请求，**Then** 系统解析出工具名称和参数
2. **Given** 工具执行完成，**When** 结果返回给 LLM，**Then** LLM 基于结果生成最终回复

---

### Edge Cases

- LLM API 超时或网络不可达时怎么办？→ 返回友好错误提示，不崩溃
- API Key 未配置或失效时怎么办？→ 首次运行引导用户配置
- LLM 返回格式异常（非预期 JSON）时怎么办？→ 降级为纯文本回复
- 并发请求时如何处理？→ 串行处理，MVP 阶段不支持并发
- 上下文过长超过模型 token 限制时怎么办？→ 截断旧上下文，保留最近对话

## Requirements

### Functional Requirements

- **FR-001**: 系统 MUST 提供统一的 LLM 调用接口，屏蔽不同模型 API 的差异
- **FR-002**: 系统 MUST 支持智谱 API 和 DeepSeek API 两个模型提供商
- **FR-003**: 系统 MUST 支持运行时切换模型，无需重启
- **FR-004**: 系统 MUST 将以下个人上下文组装到每次 LLM 调用的 system prompt 中：
  - 用户记忆（来自 memory/ 模块）
  - 动态记忆（来自 Mem0）
  - 指令列表（来自 instruction/ 模块）
  - 知识上下文（来自 knowledge/ 模块的检索结果）
- **FR-005**: 系统 MUST 支持工具调用（function calling），至少定义以下工具：
  - Shell 命令执行
  - 文件读写
  - 知识库检索
- **FR-006**: 系统 MUST 在 LLM 调用失败时返回明确的错误信息，而非抛出未处理异常
- **FR-007**: 系统 MUST 将对话历史传递给 LLM，支持多轮上下文
- **FR-008**: 系统 SHOULD 支持流式输出（逐字显示回复），提升交互体验
- **FR-009**: 系统 MUST 通过配置文件管理 API Key，不在代码中硬编码

### Key Entities

- **LLMAdapter**: 统一调用接口，屏蔽模型差异
- **Prompt**: 组装后的完整 prompt（system + context + history + user message）
- **ToolDefinition**: 工具定义（名称、描述、参数 schema）
- **LLMResponse**: 模型返回结果（文本内容 + 可选的工具调用指令）

## Success Criteria

### Measurable Outcomes

- **SC-001**: 用户发送消息后，2 秒内开始收到回复（首 token 延迟）
- **SC-002**: 模型切换在 1 秒内完成，无需重启
- **SC-003**: 用户无需关心底层使用的是哪个模型，体验一致；Friday 是个人助手，不依赖任何项目
- **SC-004**: LLM 调用失败时，用户看到友好的中文错误提示，而非技术报错
- **SC-005**: 多轮对话中 LLM 能记住前文内容并连贯回答

## Assumptions

- 用户已有智谱和/或 DeepSeek 的 API Key
- MVP 阶段 memory/knowledge/instruction 模块尚未实现，上下文组装接口先定义，传入数据可为空
- API Key 存储在本地 `~/.friday/config.yaml` 中
- 智谱和 DeepSeek 的 API 兼容 OpenAI 格式（或可通过适配层兼容）
- MVP 阶段不支持并发 LLM 调用，请求串行处理
- 流式输出为 SHOULD 级别，MVP 可先实现非流式
