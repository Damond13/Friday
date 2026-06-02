# 任务清单：知识库模块

**Input**: Design documents from `/specs/003-knowledge-base/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/knowledge-api.md

**Tests**: 包含核心逻辑的单元测试任务（store, fts, vector, adapter）

**Organization**: 任务按用户故事分组，支持独立实现和测试

## 格式: `[ID] [P?] [Story] 描述`

- **[P]**: 可并行执行（不同文件，无依赖）
- **[Story]**: 所属用户故事（US1, US2, US3）
- 包含具体文件路径

---

## Phase 1: Setup（项目初始化）

**目的**: 安装依赖、创建模块结构

- [x] T001 安装依赖 chromadb, watchdog, sentence-transformers, jieba 到 pyproject.toml
- [x] T002 创建 knowledge 模块文件结构 src/friday/knowledge/（__init__.py, store.py, fts.py, vector.py, embedding.py, watcher.py, adapter.py）
- [x] T003 创建测试文件 tests/unit/test_store.py, test_fts.py, test_vector.py, test_adapter.py

---

## Phase 2: Foundational（基础组件）

**目的**: 所有用户故事共用的底层组件，MUST 完成后才能开始用户故事

**⚠️ 关键**: 用户故事工作不能在此阶段完成前开始

- [x] T004 实现 Note 和 SearchResult 数据类 src/friday/knowledge/store.py
- [x] T005 实现本地 embedding adapter src/friday/knowledge/embedding.py（加载 bge-m3 模型，提供 embed_texts 接口）
- [x] T006 [P] 实现 FTS5 索引管理 src/friday/knowledge/fts.py（建表、插入、删除、搜索，jieba 分词）
- [x] T007 [P] 实现 ChromaDB 向量索引管理 src/friday/knowledge/vector.py（PersistentClient、collection 管理、upsert、搜索）
- [x] T008 实现笔记文件管理 src/friday/knowledge/store.py（创建 Markdown 文件、读取、删除、列出，含 YAML front matter）

**Checkpoint**: 底层组件就绪，用户故事实现可以开始

---

## Phase 3: User Story 1 - 知识录入 (Priority: P1) 🎯 MVP

**Goal**: 用户能通过对话或 /note 命令录入知识，自动建立索引

**Independent Test**: 通过 /note 命令写入笔记，验证文件创建和 FTS5/ChromaDB 索引建立

### 单元测试

- [x] T009 [P] [US1] 笔记文件管理测试 tests/unit/test_store.py（创建、读取、删除、列表、YAML front matter 解析）
- [x] T010 [P] [US1] FTS5 索引测试 tests/unit/test_fts.py（建表、插入、搜索、删除、中文分词）
- [x] T011 [P] [US1] ChromaDB 向量索引测试 tests/unit/test_vector.py（upsert、搜索、删除）

### 实现

- [x] T012 [US1] 实现 adapter.py 中的 add_note() src/friday/knowledge/adapter.py（调用 store 创建文件 → fts 插入索引 → vector 插入向量）
- [x] T013 [US1] 实现 adapter.py 中的 delete_note() 和 list_notes() src/friday/knowledge/adapter.py
- [x] T014 [US1] 在 cli/slash.py 注册 /note 斜杠命令，调用 knowledge.adapter.add_note()
- [x] T015 [US1] 在 cli/repl.py 中识别"记一下 xxx"意图，调用 knowledge.adapter.add_note()
- [x] T016 [US1] 更新 knowledge/__init__.py 导出公共 API

**Checkpoint**: 用户可以通过对话或 /note 命令录入知识，索引自动建立

---

## Phase 4: User Story 2 - 知识检索 (Priority: P2)

**Goal**: 用户通过关键词、语义或 RAG 三种方式检索知识

**Independent Test**: 先手动写入测试笔记，用 /search 和自然语言验证检索结果

### 单元测试

- [x] T017 [P] [US2] 统一检索接口测试 tests/unit/test_adapter.py（search 三种模式、降级策略、rag_query）

### 实现

- [x] T018 [US2] 实现 adapter.py 中的 search() src/friday/knowledge/adapter.py（fts 模式、vector 模式、auto 合并去重、降级策略）
- [x] T019 [US2] 实现 adapter.py 中的 rag_query() src/friday/knowledge/adapter.py（调用 search → 拼 prompt → 调 llm.chat）
- [x] T020 [US2] 在 cli/slash.py 注册 /search 斜杠命令，调用 knowledge.adapter.search()
- [x] T021 [US2] 在 cli/display.py 添加检索结果展示函数 show_search_results()

**Checkpoint**: 用户可以通过 /search 命令和自然语言检索知识

---

## Phase 5: User Story 3 - 目录监控与增量索引 (Priority: P3)

**Goal**: 文件变化时自动增量更新索引，无需手动操作

**Independent Test**: 在知识目录下新增/修改/删除文件，验证索引自动同步

### 实现

- [x] T022 [US3] 实现 watcher.py src/friday/knowledge/watchdog 事件处理（on_created、on_modified、on_deleted → 增量更新索引）
- [x] T023 [US3] 实现 start_watcher() 和 stop_watcher() src/friday/knowledge/watcher.py
- [x] T024 [US3] 在 cli/repl.py 的 run_repl() 中启动和停止 watcher
- [x] T025 [US3] 实现增量索引逻辑：新增文件 → 插入索引，修改文件 → 先删后插，删除文件 → 移除索引

**Checkpoint**: 文件变化自动同步索引，无需手动操作

---

## Phase 6: Polish & 跨模块整合

**目的**: 跨故事优化和最终验证

- [x] T026 [P] 运行全部测试，确保通过 tests/unit/
- [x] T027 [P] 按 quickstart.md 验证完整流程
- [x] T028 更新 knowledge/__init__.py 最终导出清单

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: 无依赖，立即开始
- **Phase 2 (Foundational)**: 依赖 Phase 1 — 阻塞所有用户故事
- **Phase 3 (US1)**: 依赖 Phase 2
- **Phase 4 (US2)**: 依赖 Phase 2 + Phase 3（需要 add_note 提供测试数据）
- **Phase 5 (US3)**: 依赖 Phase 2 + Phase 3（需要索引基础）
- **Phase 6 (Polish)**: 依赖所有用户故事完成

### Parallel Opportunities

- Phase 2 中 T006 (fts.py) 和 T007 (vector.py) 可并行
- Phase 3 中 T009, T010, T011 测试任务可并行
- Phase 4 中测试和展示函数可并行

---

## Implementation Strategy

### MVP (仅 User Story 1)

1. Phase 1: Setup → 安装依赖，创建文件
2. Phase 2: Foundational → 底层组件就绪
3. Phase 3: US1 → 知识录入功能完整
4. **验证**: 用 /note 命令录入笔记，确认文件和索引建立

### Incremental Delivery

1. Setup + Foundational → 基础就绪
2. US1 → 录入可用（MVP）
3. US2 → 检索可用
4. US3 → 自动监控可用
5. Polish → 最终验证

---

## Notes

- 每个文件不超过 200 行，函数不超过 30 行
- 类型注解必须加
- embedding 用本地 bge-m3 模型，不调 API
- ChromaDB 不可用时降级为仅 FTS5
