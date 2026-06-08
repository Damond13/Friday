# Feature Specification: 知识库添加工具

**Feature Branch**: `013-knowledge-add-tool`

**Created**: 2026-06-07

**Status**: Draft

**Input**: 用户描述: "添加 knowledge_add 工具。当前 LLM Agent 只有 knowledge_search 工具，无法通过工具调用向知识库添加笔记。用户在交互模式中要求"添加到知识库"时，LLM 只能用 shell_execute 执行 Python 代码来创建笔记，这种方式不可靠且容易失败。需要新增一个 knowledge_add 工具，让 LLM 能直接通过工具调用向知识库添加笔记。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 通过对话向知识库添加笔记 (Priority: P1)

用户在交互模式中告诉 Friday 一条信息并要求存储到知识库，Friday 通过工具调用直接完成录入，用户看到录入成功的确认。

**Why this priority**: 这是知识库最核心的交互场景。没有这个能力，用户无法通过对话自然地积累知识，只能依赖斜杠命令或手动编辑文件。

**Independent Test**: 可以通过发送"把 xxx 添加到知识库"消息，验证 Friday 是否调用了知识添加工具并返回成功确认来独立测试。

**Acceptance Scenarios**:

1. **Given** 用户在交互模式中，**When** 用户说"帮我记住：女朋友的名字叫张莉玉"，**Then** Friday 调用知识添加工具创建笔记，回复确认信息
2. **Given** 用户在交互模式中，**When** 用户说"把刚才的信息添加到知识库"，**Then** Friday 从上下文中提取信息，调用知识添加工具创建笔记
3. **Given** 用户在交互模式中，**When** 用户说"记一下 Python 装饰器的用法：xxx"，**Then** Friday 调用知识添加工具，以"Python 装饰器的用法"为标题创建笔记

---

### User Story 2 - 工具调用失败的优雅处理 (Priority: P2)

当知识添加操作失败时（如内容为空），Friday 应给出清晰的错误提示，而不是静默失败或崩溃。

**Why this priority**: 错误处理保证用户体验的可靠性，避免用户困惑。

**Independent Test**: 可以通过发送空内容或触发异常的消息，验证 Friday 是否给出有意义的错误提示。

**Acceptance Scenarios**:

1. **Given** 用户要求添加知识，**When** 提供的内容为空，**Then** Friday 提示内容不能为空，不创建笔记
2. **Given** 用户要求添加知识，**When** 存储系统出错，**Then** Friday 提示添加失败，建议稍后重试

---

### Edge Cases

- 标题超长时如何处理？— 自动截断标题到合理长度
- 内容包含特殊字符时是否正常存储？— 应正常存储，不丢失内容
- 用户一次要求添加多条信息时如何处理？— 每条信息单独创建一个笔记

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统必须提供知识添加工具，允许 AI 助手通过工具调用向知识库创建笔记
- **FR-002**: 工具必须接受标题和内容作为输入参数
- **FR-003**: 工具必须支持可选的标签参数，用于笔记分类
- **FR-004**: 工具调用成功后，必须返回创建结果（笔记 ID 和确认信息）
- **FR-005**: 工具调用失败时，必须返回有意义的错误信息
- **FR-006**: 内容为空时，工具必须拒绝创建并返回错误
- **FR-007**: 标题过长时，工具必须自动截断到合理长度

### Key Entities

- **笔记**: 包含标题、内容、标签、创建时间。标题为必填，内容为必填，标签为可选。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 用户说"把 xxx 添加到知识库"后，100% 的情况下 Friday 通过工具调用完成录入（而非 shell_execute）
- **SC-002**: 笔记添加操作在 1 秒内完成
- **SC-003**: 添加成功的笔记可通过知识库检索找到
- **SC-004**: 用户无需了解底层存储细节即可完成知识录入

## Assumptions

- 工具复用现有的知识库存储层（笔记文件 + FTS 索引 + 向量索引），不新建存储机制
- 工具仅面向 AI 助手的工具调用场景，不直接暴露给用户作为斜杠命令（已有 `/note` 命令）
- 标题最大长度默认 100 字符，超出自动截断
- 工具与现有 `knowledge_search` 工具并列，在同一工具列表中注册
