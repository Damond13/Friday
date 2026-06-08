# Tasks: 知识库添加工具

**Input**: Design documents from `/specs/013-knowledge-add-tool/`

**Prerequisites**: plan.md (required), spec.md (required)

**Tests**: 工具定义和执行器涉及数据存储，按风险评估需要测试。

**Organization**: 按用户故事分组，支持独立实现和验证。

## Format: `[ID] [G{n}] [P?] [Story] Description`

- **[G{n}]**: 并行组号，同组可并行
- **[P]**: 可并行（不同文件，无依赖）
- **[Story]**: 所属用户故事（US1/US2/US3）

## Phase 1: User Story 1 - 通过对话向知识库添加笔记 (Priority: P1) 🎯 MVP

**Goal**: LLM Agent 能通过 knowledge_add 工具调用向知识库添加笔记

**Independent Test**: 发送"帮我记住 xxx"，验证 Friday 调用 knowledge_add 工具而非 shell_execute

### Implementation for User Story 1

- [x] T001 [G0] [US1] 新增 KNOWLEDGE_ADD 工具定义 in `src/friday/llm/tools.py`：参照 KNOWLEDGE_SEARCH 模式，定义 KNOWLEDGE_ADD（参数：title 必填、content 必填、tags 可选），将其加入 `get_tool_definitions()` 返回列表
- [x] T002 [G1] [US1] 新增 `_exec_knowledge_add` 执行器 in `src/friday/llm/executors.py`：实现异步执行器，校验 title/content 非空，title 超 100 字符自动截断，调用 `knowledge.adapter.add_note(title, content, tags)` 创建笔记，返回笔记 ID 和标题；注册到 `_register("knowledge_add", _exec_knowledge_add)`
- [x] T003 [G2] [US1] 更新工具定义测试 in `tests/unit/test_tools.py`：更新 `test_get_tool_definitions_returns_list` 的断言从 4 改为 5，更新 `test_tool_names` 的预期名称集合加入 `"knowledge_add"`，新增 `test_knowledge_add_requires_title_and_content` 验证必填参数，新增 `test_knowledge_add_has_optional_tags` 验证 tags 为可选参数

**Checkpoint**: 此时应能通过 pytest 验证工具定义正确，knowledge_add 工具已注册

---

## Phase 2: User Story 2 - 工具调用失败的优雅处理 (Priority: P2)

**Goal**: 知识添加操作失败时（内容为空、存储出错），返回有意义的错误信息

**Independent Test**: 验证空内容、超长标题等边界场景返回正确错误

### Implementation for User Story 2

- [x] T004 [G0] [US2] 新增执行器边界测试 in `tests/unit/test_executors.py`：测试 `_exec_knowledge_add` 的边界场景——空 title 返回错误、空 content 返回错误、超长 title 自动截断到 100 字符、纯空白 title/content 返回错误

**Checkpoint**: 所有边界测试通过，错误处理完善

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (US1)**: 无前置依赖，可立即开始
- **Phase 2 (US2)**: 依赖 Phase 1 完成（执行器实现后才能测试边界场景）

### Within Phase 1

- T001 先行（定义工具）
- T002 依赖 T001（执行器引用工具定义，但修改不同文件可并行）
- T003 依赖 T001 和 T002（测试验证工具定义和注册）

### Within Phase 2

- T004 依赖 Phase 1 完成

---

## Parallel Groups

| Group | Tasks  | Depends On | Notes              |
|-------|--------|------------|--------------------|
| G0    | T001   | —          | tools.py 工具定义  |
| G1    | T002   | G0         | executors.py 执行器 |
| G2    | T003   | G1         | 测试验证           |
| G3    | T004   | G2         | 边界测试           |

**Max parallelism**: 1
**Total groups**: 4

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. 完成 T001（tools.py 工具定义）
2. 完成 T002（executors.py 执行器）
3. 完成 T003（测试验证）
4. 运行 `pytest tests/unit/test_tools.py -v` 确认通过

### Full Delivery

5. 完成 T004（边界测试）
6. 运行测试确认通过
7. 手动启动 Friday，发送"帮我记住 xxx"验证工具调用
