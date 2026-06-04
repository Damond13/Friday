# Tasks: Agent 工具调用循环

**Input**: Design documents from `/specs/008-agent-tool-loop/`

**Prerequisites**: plan.md (required), spec.md (required), data-model.md, contracts/tool-executors.md

**Tests**: 未在 spec 中明确要求 TDD，测试任务放在 Polish 阶段。

**Organization**: Tasks grouped by user story，每个 story 可独立实现和测试。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Agent 循环所需的基础类型和工具执行器，所有 User Story 共享

**⚠️ CRITICAL**: US1/US2/US3 的实现都依赖本阶段完成

- [x] T001 新增 ToolResult 数据类到 `src/friday/llm/types.py`（字段：tool_call_id, success, output）
- [x] T002 创建 `src/friday/llm/executors.py`：工具执行器注册表 + 4 个执行器实现（shell_execute 调用 executor.execute()，file_read 读文件，file_write 写文件，knowledge_search 调用 adapter.search()）

**Checkpoint**: ToolResult 类型就绪，4 个工具执行器可独立调用

---

## Phase 2: User Story 1 - 基础工具调用 (Priority: P1) 🎯 MVP

**Goal**: 用户问"当前目录有什么文件"，Friday 调用 shell_execute 执行 ls，拿结果后用自然语言回复

**Independent Test**: 在 REPL 中输入"当前目录有什么文件"，验证 Friday 调用工具并给出准确回答

### Implementation

- [x] T003 [US1] 创建 `src/friday/llm/agent.py`：实现 `run_agent_loop(messages, context)` 函数，包含 LLM 调用 → tool_call 检测 → 工具执行 → 结果回传的循环逻辑，最大 10 轮，返回 AgentResult(reply, messages, tool_calls_count)
- [x] T004 [US1] 修改 `src/friday/cli/repl.py`：将 `_stream_reply()` 改为调用 `run_agent_loop()`，传入工具定义和 PromptContext，展示最终回复
- [x] T005 [US1] 在 `src/friday/cli/display.py` 中新增 `show_tool_call(name, arguments)` 和 `show_tool_result(success, output)` 展示函数，在 agent loop 回调中使用

**Checkpoint**: 在 REPL 中输入需要工具的问题，Friday 能调用工具并回复；普通对话不受影响

---

## Phase 3: User Story 2 - 多轮工具调用 (Priority: P2)

**Goal**: 用户给复杂指令时，Friday 能连续调用多个工具完成任务（如先读文件再搜索知识库）

**Independent Test**: 输入"读取 README.md 的内容然后总结"，验证 Friday 连续调用 file_read + LLM 总结

### Implementation

- [x] T006 [US2] 增强 `src/friday/llm/agent.py`：验证多轮循环的稳定性，处理 LLM 连续返回 tool_call 的场景，确保每轮 tool 消息正确追加，超限时优雅停止

**Checkpoint**: 输入多步任务，Friday 连续调用工具直到完成；输入简单问题仍正常回复

---

## Phase 4: User Story 3 - 安全确认机制 (Priority: P3)

**Goal**: 危险操作（rm、覆写文件）执行前向用户确认，用户拒绝则取消

**Independent Test**: 让 Friday 执行 `rm` 命令，验证弹出确认提示；用户拒绝后操作取消

### Implementation

- [x] T007 [US3] 修改 `src/friday/cli/repl.py`：在 `run_repl()` 启动时调用 `set_confirm_callback()` 注册 CLI 层确认函数（使用 Rich Confirm 弹窗），使 shell_execute 的安全分级生效
- [x] T008 [US3] 修改 `src/friday/llm/executors.py`：file_write 执行器增加覆写检查——目标文件已存在时，通过确认回调请求用户许可，拒绝则返回 ToolResult(success=False)

**Checkpoint**: 危险 shell 命令和文件覆写都触发确认；安全命令（ls、cat）直接执行

---

## Phase 5: Polish & Tests

**Purpose**: 单元测试和收尾

- [x] T009 创建 `tests/unit/test_agent.py`：测试普通对话不触发工具、单个 tool_call 路由、多 tool_call 执行、执行错误回传、超限停止

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Foundational)**: 无依赖，立即开始
- **Phase 2 (US1)**: 依赖 Phase 1 完成
- **Phase 3 (US2)**: 依赖 Phase 2 完成（在 US1 基础上验证）
- **Phase 4 (US3)**: 依赖 Phase 2 完成（需 executors 和 REPL 就绪）
- **Phase 5 (Polish)**: 依赖所有 User Story 完成

### User Story Dependencies

- **US1 (P1)**: 依赖 Foundational — 无其他 story 依赖
- **US2 (P2)**: 依赖 US1（在 agent loop 基础上验证多轮）
- **US3 (P3)**: 依赖 US1（需 REPL 和 executors 就绪），与 US2 无依赖，可并行

### Parallel Opportunities

- T001 和 T002 可并行（不同关注点，但 T002 引用 T001 的类型，建议顺序执行）
- T007 和 T008 可并行（不同文件：repl.py 和 executors.py）
- Phase 3 和 Phase 4 可并行（US2 和 US3 无相互依赖）

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Foundational (T001, T002)
2. Complete Phase 2: US1 (T003, T004, T005)
3. **STOP and VALIDATE**: 在 REPL 中测试基础工具调用
4. 可用后继续后续 story

### Incremental Delivery

1. Phase 1 → 工具执行器就绪
2. Phase 2 → MVP：基础工具调用可用
3. Phase 3 → 多轮工具调用可用
4. Phase 4 → 安全确认就绪
5. Phase 5 → 测试覆盖

---

## Notes

- prompts.py 的 BASE_SYSTEM_PROMPT 增强已在上一个 commit 完成，不包含在本次任务中
- repl.py 的 `_build_context()` 已在上一个 commit 添加，不包含在本次任务中
- agent.py 是本次的核心新文件，预计 ~120 行
- executors.py 是新增文件，预计 ~100 行
