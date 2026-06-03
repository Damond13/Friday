# Tasks: 共享 Embedding 模型实例

**Input**: Design documents from `/specs/007-share-embedding-model/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, quickstart.md

**Tests**: US1 新增单元测试验证共享实例，US2 运行现有测试套件确认无回归

**Organization**: 按用户故事分组，支持独立实现和验证

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行执行（不同文件，无依赖）
- **[Story]**: 所属用户故事（US1, US2）
- 包含精确文件路径

---

## Phase 1: Setup (共享基础设施)

**Purpose**: 项目已存在，无需额外初始化

*无任务 — 项目结构和依赖已就绪*

---

## Phase 2: Foundational (阻塞性前置任务)

**Purpose**: 导出共享模型获取函数，是所有后续任务的前置依赖

**⚠️ CRITICAL**: 必须完成后才能进入 Phase 3

- [x] T001 在 `src/friday/knowledge/embedding.py` 新增 `get_shared_model()` 公开函数，复用现有 `_get_model()` 的 lru_cache 实例

**Checkpoint**: `from friday.knowledge.embedding import get_shared_model` 可正常导入

---

## Phase 3: User Story 1 - 模型只加载一次 (Priority: P1) 🎯 MVP

**Goal**: 知识库和动态记忆共享同一个 SentenceTransformer 模型实例，内存占用从 ~4GB 降至 ~2GB

**Independent Test**: 单元测试验证 `get_shared_model()` 返回同一实例，Mem0 内部模型被替换为共享实例

### Tests for User Story 1

- [x] T002 [P] [US1] 新增单元测试验证共享模型实例，在 `tests/unit/test_embedding_share.py`，mock Mem0 初始化后检查 `embedding_model.model is get_shared_model()`

### Implementation for User Story 1

- [x] T003 [US1] 在 `src/friday/memory/dynamic.py` 的 `_init_memory()` 中，Mem0 初始化成功后，将 `memory.embedding_model.model` 替换为 `get_shared_model()` 返回的共享实例
- [x] T004 [US1] 在 `src/friday/memory/dynamic.py` 的模型注入逻辑外包裹 try/except，注入失败时仅记录日志不影响 Mem0 正常初始化
- [x] T005 [US1] 运行 T002 新增的单元测试确认通过

**Checkpoint**: 知识库和动态记忆使用同一模型实例，功能正常

---

## Phase 4: User Story 2 - 共享后功能不受影响 (Priority: P1)

**Goal**: 共享模型实例后，全部现有功能与共享前完全一致

**Independent Test**: 运行 `uv run pytest tests/ -v`，260 passed, 2 skipped

### Verification for User Story 2

- [x] T006 [US2] 运行全部自动化测试 `uv run pytest tests/ -v`，确认无回归

**Checkpoint**: 全部测试通过，功能验证完毕

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: 最终验证和提交

- [x] T007 运行 quickstart.md 全部 4 个验证步骤，确认知识库搜索、动态记忆、共享实例均正常
- [ ] T008 提交代码并推送到远程仓库

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 无依赖，跳过
- **Foundational (Phase 2)**: 无依赖 — 阻塞所有用户故事
- **User Story 1 (Phase 3)**: 依赖 Phase 2 完成
- **User Story 2 (Phase 4)**: 依赖 Phase 3 完成（需要实现后才能验证）
- **Polish (Phase 5)**: 依赖 Phase 4 完成

### Task Dependencies

```
T001 → T002, T003 (T002 并行) → T004 → T005 → T006 → T007 → T008
```

### Parallel Opportunities

- 本功能改动范围小（2 个文件），无并行机会，建议顺序执行

---

## Implementation Strategy

### MVP First (Phase 2 + Phase 3)

1. T001: 导出共享模型函数
2. T002 + T003: 写单元测试（T002）和注入共享模型（T003）可并行
3. T004: 错误隔离
4. T005: 运行 US1 单元测试
4. **STOP and VALIDATE**: 确认模型实例共享成功

### Full Delivery

1. MVP 完成 → T005 运行全部测试
2. T006 运行完整验证
3. T007 提交推送

---

## Notes

- 本次改动仅涉及 `knowledge/embedding.py` 和 `memory/dynamic.py` 两个文件
- 编码参数差异（normalize_embeddings vs convert_to_numpy）是调用时参数，共享实例安全
- 错误隔离保证 Mem0 初始化失败不影响知识库功能
