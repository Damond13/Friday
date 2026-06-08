# Tasks: 指令系统存储统一到知识库

**Input**: Design documents from `/specs/014-unify-instruction-storage/`

**Prerequisites**: plan.md (required), spec.md (required), research.md

## Format: `[ID] [G{n}] [P?] [Story?] Description`

- **[G{n}]**: Parallel Group number
- **[P]**: Can run in parallel within group
- **[Story]**: Which user story (US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Foundational — 索引层 type 字段支持

**Purpose**: FTS 和 ChromaDB 增加 type 字段，支持按类型过滤。这是所有用户故事的前置条件。

**⚠️ CRITICAL**: 所有 US 工作必须等此阶段完成

- [x] T001 [G0] [P] FTS5 增加 type 列：`notes_fts` 表和 FTS 虚拟表新增 `type TEXT DEFAULT 'note'` 字段，触发器同步更新，`insert()` 增加 `entry_type` 参数，`search()` 增加 `entry_type` 过滤。数据库迁移用 `ALTER TABLE`。文件：`src/friday/knowledge/fts.py`
- [x] T002 [G0] [P] ChromaDB 增加 type metadata：`upsert()` metadata 新增 `"type"` 字段（默认 `"note"`），`search()` 增加 `entry_type` 参数用 `where` 过滤。文件：`src/friday/knowledge/vector.py`
- [x] T003 [G1] 知识适配器新增指令索引函数：在 `knowledge/adapter.py` 中新增 `index_instruction(instr_id, trigger, content, keywords, file_path)` 调用 FTS 和 vector 写入 `type="instruction"` 的索引，新增 `search_instructions(query, limit)` 按 `type="instruction"` 过滤检索，新增 `delete_instruction_index(instr_id)` 清除索引。文件：`src/friday/knowledge/adapter.py`

**Checkpoint**: 索引层支持 type 区分，指令可以写入和检索 FTS/ChromaDB

---

## Phase 2: User Story 1 — 教会并执行指令 (Priority: P1) 🎯 MVP

**Goal**: 用户通过对话教会 Friday 新指令，后续用语义相近的措辞能触发执行

**Independent Test**: 教会一条"部署"指令 → 用"推到线上"搜索 → 语义匹配成功

### Implementation for User Story 1

- [x] T004 [G2] [P] [US1] 指令适配器改造：`instruction/adapter.py` 的 `teach()` 末尾调用 `knowledge.adapter.index_instruction()` 建立索引；`match()` 改为调用 `knowledge.adapter.search_instructions()` 用语义检索替代纯文本匹配；新增 `search_instructions(query, limit)` 函数对外暴露。文件：`src/friday/instruction/adapter.py`
- [x] T005 [G2] [P] [US1] 新增 instruction_add 和 instruction_search 工具定义：参照现有 `KNOWLEDGE_ADD` 模式，在 `tools.py` 中新增 `INSTRUCTION_ADD`（必填：trigger, actions；可选：name, keywords, type）和 `INSTRUCTION_SEARCH`（必填：query；可选：limit），注册到 `get_tool_definitions()`。文件：`src/friday/llm/tools.py`
- [x] T006 [G3] [US1] 新增 instruction_add 和 instruction_search 执行器：`executors.py` 中新增 `_exec_instruction_add`（校验参数 → 调用 `instruction.adapter.teach()` → 返回结果）和 `_exec_instruction_search`（调用 `instruction.adapter.search_instructions()` → 格式化输出），注册执行器。文件：`src/friday/llm/executors.py`

**Checkpoint**: US1 完成 — 可以通过工具调用教会和检索指令

---

## Phase 3: User Story 2 — 查看、管理和删除指令 (Priority: P2)

**Goal**: 用户可以查看已有指令列表和删除指定指令

**Independent Test**: 教会指令 → 查看列表包含该指令 → 删除 → 列表不再包含

### Implementation for User Story 2

- [x] T007 [G4] [P] [US2] 指令适配器补充：`instruction/adapter.py` 的 `remove()` 末尾调用 `knowledge.adapter.delete_instruction_index()` 清除索引。文件：`src/friday/instruction/adapter.py`
- [x] T008 [G4] [P] [US2] 新增 instruction_list 和 instruction_delete 工具定义：`tools.py` 中新增 `INSTRUCTION_LIST`（无必填参数）和 `INSTRUCTION_DELETE`（必填：name），注册到 `get_tool_definitions()`。文件：`src/friday/llm/tools.py`
- [x] T009 [G5] [US2] 新增 instruction_list 和 instruction_delete 执行器：`executors.py` 中新增 `_exec_instruction_list`（调用 `instruction.adapter.list_instructions()` → 格式化为列表输出）和 `_exec_instruction_delete`（调用 `instruction.adapter.remove()` → 返回结果），注册执行器。文件：`src/friday/llm/executors.py`

**Checkpoint**: US2 完成 — 可以查看和删除指令

---

## Phase 4: 测试同步维护

**Purpose**: 按风险评估更新自动化测试（高风险：索引层和执行器）

- [x] T010 [G6] [P] 更新 FTS 测试：在 `tests/unit/test_fts.py` 中新增测试类 `TestTypeFiltering`：测试 insert 带 entry_type 参数、search 带 entry_type 过滤、默认 type 为 note。文件：`tests/unit/test_fts.py`
- [x] T011 [G6] [P] 更新 Vector 测试：在 `tests/unit/test_vector.py` 中新增测试：upsert 带 type metadata、search 带 entry_type 过滤、默认 type 为 note。文件：`tests/unit/test_vector.py`
- [x] T012 [G6] [P] 更新工具定义测试：在 `tests/unit/test_tools.py` 中更新 `test_get_tool_definitions_returns_list` 的数量断言（5→9）、更新 `test_tool_names` 新增 4 个指令工具名、新增 `test_instruction_add_requires_trigger_and_actions`、`test_instruction_search_defaults`、`test_instruction_delete_requires_name` 测试。文件：`tests/unit/test_tools.py`
- [x] T013 [G6] [P] 新增指令执行器测试：创建 `tests/unit/test_instruction_executors.py`，测试 _exec_instruction_add（空 trigger 报错、成功添加）、_exec_instruction_search（返回格式化结果）、_exec_instruction_list（返回列表）、_exec_instruction_delete（成功删除、不存在时失败）。文件：`tests/unit/test_instruction_executors.py`
- [x] T014 [G6] [P] 更新指令适配器测试：在 `tests/unit/test_instruction_adapter.py` 中新增测试：teach 后验证索引被创建、match 使用语义检索返回结果、remove 后验证索引被清除。文件：`tests/unit/test_instruction_adapter.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Foundational)**: 无依赖，立即开始。G0 并行 → G1 串行
- **Phase 2 (US1)**: 依赖 Phase 1 完成。G2 并行 → G3 串行
- **Phase 3 (US2)**: 依赖 Phase 2 完成。G4 并行 → G5 串行
- **Phase 4 (Tests)**: 依赖 Phase 3 完成。G6 全部并行

### User Story Dependencies

- **US1 (P1)**: 依赖索引层（Phase 1）
- **US2 (P2)**: 依赖 US1（instruction/adapter.py 改动基于 US1 的基础）

### Within Each Phase

- FTS (T001) 和 Vector (T002) 并行，互不影响
- Knowledge adapter (T003) 依赖 FTS 和 Vector 改动完成
- Tools 定义和 instruction adapter 改动可并行（不同文件）
- Executors 依赖对应的 tools 定义完成

---

## Parallel Groups

| Group | Tasks | Depends On | Notes |
|-------|-------|------------|-------|
| G0    | T001, T002 | — | FTS + Vector 改动并行，不同文件 |
| G1    | T003 | G0 | Knowledge adapter 依赖 FTS/Vector |
| G2    | T004, T005 | G1 | US1: adapter + tools 并行，不同文件 |
| G3    | T006 | G2 | US1: executors 依赖 tools 定义 |
| G4    | T007, T008 | G3 | US2: adapter + tools 并行，不同文件 |
| G5    | T009 | G4 | US2: executors 依赖 tools 定义 |
| G6    | T010, T011, T012, T013, T014 | G5 | 测试全部并行，不同文件 |

**Max parallelism**: 5
**Total groups**: 7

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: 索引层 type 支持
2. Complete Phase 2: 教会 + 执行指令
3. **STOP and VALIDATE**: 测试教会指令 → 语义检索 → 执行
4. 可以直接使用

### Incremental Delivery

1. Phase 1 → 索引基础就绪
2. Phase 2 → US1 可用（教会 + 执行）— MVP
3. Phase 3 → US2 可用（管理 + 删除）
4. Phase 4 → 测试覆盖完成
