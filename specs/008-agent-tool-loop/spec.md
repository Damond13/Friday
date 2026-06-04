# Feature Specification: Agent 工具调用循环

**Feature Branch**: `008-agent-tool-loop`

**Created**: 2026-06-04

**Status**: Draft

**Input**: 实现 Friday 的核心 Agent 循环：LLM 工具调用 + 执行 + 结果回传的完整闭环

## 背景与问题

Friday 当前已实现 LLM 适配层（spec-001）、CLI 交互壳（spec-002）、知识库（spec-003）、执行器（spec-004）、指令学习（spec-005）、双层记忆（spec-006）等模块。但这些模块是割裂的——用户在交互模式中和 Friday 对话时，Friday 只是一个"纯聊天"机器人，无法真正调用任何能力。

具体问题：
1. `tools.py` 已定义了 4 个工具定义（shell_execute、file_read、file_write、knowledge_search），但 REPL 从未将它们传给 LLM
2. LLM 返回 tool_call 时没有识别和执行逻辑
3. 工具执行结果无法回传给 LLM 继续推理
4. 缺少工具执行的安全确认机制

本功能是 Friday 从"聊天机器人"进化为"AI Agent"的关键一步。

## User Scenarios & Testing

### User Story 1 - 基础工具调用（Priority: P1）

用户在交互模式中问 Friday "当前目录有哪些文件"，Friday 自动调用 shell_execute 工具执行 `ls`，拿到结果后用自然语言回答用户。

**Why this priority**: 这是 Agent 循环的最小闭环，验证 LLM → 工具调用 → 执行 → 结果回传 → 最终回复的完整链路。

**Independent Test**: 在 REPL 中输入需要执行命令的问题（如"当前时间"、"列出文件"），验证 Friday 能调用工具并给出准确回答。

**Acceptance Scenarios**:

1. **Given** 用户在交互模式中，**When** 输入"当前目录有什么文件"，**Then** Friday 调用 shell_execute 执行 `ls`，将结果整理后用自然语言回复
2. **Given** 用户问"帮我读一下 README.md"，**Then** Friday 调用 file_read 工具读取文件内容并展示
3. **Given** 用户问一个不需要工具的普通问题，**Then** Friday 直接用文本回复，不触发任何工具调用

---

### User Story 2 - 多轮工具调用（Priority: P2）

用户给出需要多步操作的指令，Friday 连续调用多个工具完成任务。

**Why this priority**: 真实使用场景中，复杂任务往往需要多步操作（如读取文件 → 分析内容 → 执行操作）。

**Independent Test**: 输入需要多步操作的任务（如"读取 config.yaml 看看数据库配置，然后帮我备份"），验证 Friday 能正确链式调用工具。

**Acceptance Scenarios**:

1. **Given** 用户说"读取 notes/todo.txt 的内容然后总结"，**When** Friday 读取文件后，**Then** 自动基于内容生成总结，不需要用户再次输入
2. **Given** 用户说"搜索知识库里关于 Python 的笔记"，**Then** Friday 调用 knowledge_search 工具检索，用自然语言整理结果
3. **Given** LLM 连续调用多个工具（如先读文件再搜索知识库），**Then** 每次工具执行结果都正确回传，直到得到最终回复

---

### User Story 3 - 安全确认机制（Priority: P3）

当 Friday 要执行危险操作（如删除文件、覆写重要配置）时，先向用户确认再执行。

**Why this priority**: 安全可控是 Constitution 核心原则 IV，必须在 Agent 获得执行能力的同时建立安全防线。

**Independent Test**: 触发包含危险关键词的命令，验证弹出确认提示；安全命令则直接执行。

**Acceptance Scenarios**:

1. **Given** Friday 要执行 `rm -rf /tmp/test`，**When** 命令包含 `rm` 关键词，**Then** 向用户展示命令内容并请求确认
2. **Given** 用户拒绝确认，**Then** Friday 不执行该命令，告知用户已取消，并将拒绝信息回传 LLM
3. **Given** Friday 要执行 `ls -la`，**When** 这是安全命令，**Then** 直接执行无需确认

---

### Edge Cases

- LLM 返回的 tool_call 参数格式异常（如 JSON 解析失败）时怎么办？→ 返回错误信息给 LLM，让它重新生成
- 工具执行超时时怎么办？→ 返回超时错误给 LLM，让它决定下一步
- LLM 连续调用工具次数过多（死循环）时怎么办？→ 设置最大轮次限制（默认 10 次），超限后强制停止并提示用户
- 流式输出模式下如何处理 tool_call？→ tool_call 不走流式，用非流式接口获取完整 tool_call 响应

## Requirements

### Functional Requirements

- **FR-001**: REPL 对话时必须将工具定义（shell_execute、file_read、file_write、knowledge_search）传给 LLM
- **FR-002**: 系统必须识别 LLM 返回的 tool_call 响应，并路由到对应的工具执行函数
- **FR-003**: 工具执行结果必须以 tool message 格式回传给 LLM，支持多轮循环直到 LLM 给出最终文本回复
- **FR-004**: 系统必须实现安全确认机制：危险命令（rm、rmdir、format、mkfs 等）执行前需用户确认；file_write 覆写已存在文件时也需确认
- **FR-005**: 工具执行过程必须有可视化反馈（显示正在调用哪个工具、参数是什么）
- **FR-006**: 工具执行结果必须有格式化展示（短输出直接显示，长输出由 LLM 总结）
- **FR-007**: 系统必须设置工具调用最大轮次限制，防止无限循环
- **FR-008**: shell_execute 工具的执行逻辑复用已有 executor/runner.py 的安全分级策略

### Key Entities

- **ToolCall**: LLM 返回的工具调用请求，包含工具名、参数、调用 ID
- **ToolResult**: 工具执行结果，包含执行状态（成功/失败）、输出内容、调用 ID
- **AgentLoop**: 管理多轮工具调用循环的控制器，负责"LLM 调用 → 工具执行 → 结果回传"的循环

## Success Criteria

### Measurable Outcomes

- **SC-001**: 用户在 REPL 中输入需要工具的问题时，Friday 能在 5 秒内开始执行第一个工具调用
- **SC-002**: 工具调用循环能正确处理至少 5 轮连续工具调用而不中断
- **SC-003**: 所有危险命令执行前 100% 触发用户确认
- **SC-004**: 用户能清晰看到 Friday 正在调用哪个工具、传了什么参数，信息准确无遗漏
- **SC-005**: 不需要工具的普通对话不受影响，回复速度和体验与之前一致

## Assumptions

- 当前使用的 LLM（智谱 GLM / DeepSeek）均支持 OpenAI 兼容的 function calling 格式
- 流式输出（chat_stream）和工具调用（tool_call）在单次请求中互斥——有 tool_call 时用非流式接口
- 安全命令列表参考已有 executor/runner.py 的实现，保持一致
- 文件路径安全由工具执行层负责校验，不在 Agent 循环层重复检查
- 工具调用最大轮次默认 10 次，后续可通过配置调整

## Clarifications

### Session 2026-06-04

- Q: file_write 工具是否需要安全确认？ → A: 覆写已存在文件时确认，新建文件直接写入

## Constitution Check

- **原则 I（个人化优先）**: ✅ 工具调用让 Friday 能真正帮用户做事，提升个人助手价值
- **原则 IV（安全可控）**: ✅ 安全确认机制确保用户始终掌控危险操作
- **原则 V（简洁实用）**: ✅ 工具执行过程简洁展示，结果按长度智能处理
- **模块边界**: ✅ Agent 循环属于 llm/ 层的扩展，工具执行逻辑复用 executor/，不越界
