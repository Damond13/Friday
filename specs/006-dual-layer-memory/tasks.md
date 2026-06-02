# Tasks: 双层记忆系统

**Input**: Design documents from `/specs/006-dual-layer-memory/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/memory-api.md

**Tests**: CLAUDE.md 要求"测试覆盖核心逻辑"，测试任务在 Polish 阶段执行。

**Organization**: 按用户故事组织任务，每个故事可独立实现和测试。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行执行（不同文件，无依赖）
- **[Story]**: 所属用户故事（US1, US2, US3）
- 描述包含精确文件路径

---

## Phase 1: Setup（项目初始化）

**Purpose**: 创建模块文件结构

- [x] T001 在 src/friday/memory/ 下创建 dynamic.py, files.py, adapter.py 空文件，在 tests/unit/ 下创建 test_memory_dynamic.py, test_memory_files.py 空文件

---

## Phase 2: Foundational（阻塞性前置条件）

**Purpose**: 数据模型和 Mem0 初始化配置

- [x] T002 定义数据模型在 src/friday/memory/dynamic.py：MemoryItem 数据类（id, content, metadata, score），MemorySearchResult 数据类（source, content, score, metadata），以及 Mem0 客户端初始化函数 init_memory()，使用本地 ChromaDB 配置（路径 .friday-memory/）

**Checkpoint**: 数据模型和 Mem0 初始化就绪

---

## Phase 3: User Story 1 - 动态记忆存取 (Priority: P1) 🎯 MVP

**Goal**: 用户可通过 add_memory() 添加记忆，通过 search_memories() 语义检索

**Independent Test**: add_memory("用户偏好暗色主题") 后 search_memories("颜色偏好") 返回该记忆

- [x] T003 [US1] 实现动态记忆 CRUD 在 src/friday/memory/dynamic.py：add_memory() 封装 Mem0.add()，search_memory() 封装 Mem0.search()，list_memories() 封装 Mem0.get_all()，delete_memory() 封装 Mem0.delete()。所有操作使用 user_id="friday_user" 作为默认用户标识
- [x] T004 [US1] 实现 add_memory/search_memories/list_memories/delete_memory 在 src/friday/memory/adapter.py：调用 dynamic 模块方法，返回对应类型。search_memories 暂时只搜索动态记忆层（US3 扩展为统一检索）

**Checkpoint**: 动态记忆的增删查检索功能可用

---

## Phase 4: User Story 2 - 结构化文件记忆 (Priority: P2)

**Goal**: 用户可管理决策记录和经验教训

**Independent Test**: add_decision() 写入决策，list_decisions() 返回列表

- [x] T005 [US2] 实现文件记忆管理在 src/friday/memory/files.py：定义 Decision 数据类（title, date, status, context, decision）和 Lesson 数据类（title, date, context, lesson），实现 add_decision() 追加到 decisions.md，list_decisions() 解析文件返回列表，add_lesson() 追加到 lessons-learned.md，list_lessons() 解析返回列表，get_constitution() 读取 .specify/memory/constitution.md。存储路径使用项目根目录下的 .specify/memory/
- [x] T006 [US2] 实现 add_decision/list_decisions/add_lesson/list_lessons/get_constitution 在 src/friday/memory/adapter.py：委托给 files 模块，返回对应类型

**Checkpoint**: 决策记录和经验教训的增查功能可用

---

## Phase 5: User Story 3 - 统一记忆检索 (Priority: P3)

**Goal**: search_memories() 同时搜索动态和文件记忆

**Independent Test**: 存入动态记忆和决策记录后，统一搜索返回两层结果

- [x] T007 [US3] 实现文件记忆关键词搜索在 src/friday/memory/files.py：search_files() 对 decisions.md 和 lessons-learned.md 做关键词匹配，返回 list[MemorySearchResult]（source="files"，score=1.0）
- [x] T008 [US3] 扩展 search_memories() 在 src/friday/memory/adapter.py：同时调用 dynamic.search_memory() 和 files.search_files()，合并结果按评分降序返回

**Checkpoint**: 统一检索跨两层返回合并结果

---

## Phase 6: Polish & Cross-Cutting

**Purpose**: 公共 API 导出、单元测试、端到端验证

- [x] T009 [P] 实现公共 API 导出在 src/friday/memory/__init__.py：导出 add_memory, search_memories, list_memories, delete_memory, add_decision, list_decisions, add_lesson, list_lessons, get_constitution, MemoryItem, MemorySearchResult, Decision, Lesson，定义 __all__
- [x] T010 [P] 编写动态记忆单元测试在 tests/unit/test_memory_dynamic.py：测试 add_memory 返回有效 id、search_memory 有结果、list_memories 返回列表、delete_memory 返回 bool
- [x] T011 [P] 编写文件记忆单元测试在 tests/unit/test_memory_files.py：测试 add_decision 写入文件、list_decisions 解析返回、add_lesson 写入文件、list_lessons 解析返回、get_constitution 读取内容
- [x] T012 按 quickstart.md 的 5 个验证场景端到端验证

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 无依赖，立即开始
- **Foundational (Phase 2)**: 依赖 Setup 完成
- **US1 (Phase 3)**: 依赖 Foundational — MVP 核心
- **US2 (Phase 4)**: 依赖 US1（在 adapter.py 基础上增加文件记忆接口）
- **US3 (Phase 5)**: 依赖 US1 + US2（统一检索需要两层都实现）
- **Polish (Phase 6)**: 依赖 US1-US3 全部完成

### User Story Dependencies

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational)
    ↓
Phase 3 (US1 - 动态记忆) 🎯 MVP
    ↓
Phase 4 (US2 - 文件记忆)
    ↓
Phase 5 (US3 - 统一检索)
    ↓
Phase 6 (Polish)
```

### Parallel Opportunities

- Phase 6: T009, T010, T011 可并行（不同文件）

---

## Implementation Strategy

### MVP First（仅 User Story 1）

1. 完成 Phase 1: Setup
2. 完成 Phase 2: Foundational
3. 完成 Phase 3: US1 动态记忆
4. **验证**: add_memory() → search_memories() → 结果正确

### Incremental Delivery

1. Setup + Foundational → 数据模型就绪
2. US1 动态记忆 → **MVP 可用！**
3. US2 文件记忆 → 结构化知识管理
4. US3 统一检索 → 跨层搜索
5. Polish → 测试 + 导出 + 验证
