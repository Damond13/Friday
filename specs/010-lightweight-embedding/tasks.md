# Tasks: 轻量 Embedding 模型切换

**Input**: Design documents from `/specs/010-lightweight-embedding/`

**Prerequisites**: plan.md (required), spec.md (required), research.md

**Organization**: 2 个文件改 3 行 + 数据清理，全串行。

## Format: `[ID] [G{n}] [P?] [Story] Description`

---

## Phase 1: Setup

**Purpose**: 理解当前代码，确认改动点

- [X] T001 [G0] Read current `src/friday/knowledge/embedding.py` and `src/friday/memory/dynamic.py`, confirm exact lines to change: model name, dimension constant, and Mem0 embedder config

---

## Phase 2: User Story 1 — 模型切换，降低内存 (Priority: P1) 🎯 MVP

**Goal**: 将 embedding 模型从 bge-m3 切换为 bge-small-zh-v1.5，内存增量从 ~734MB 降至 ~100MB

**Independent Test**: 启动 Friday，用 `scripts/memory_profile.py` 测量 embedding 加载后的内存增量

- [X] T002 [G1] [P] [US1] Modify `src/friday/knowledge/embedding.py`: change `_MODEL_NAME` from `"BAAI/bge-m3"` to `"BAAI/bge-small-zh-v1.5"` and `_EMBEDDING_DIM` from `1024` to `512`
- [X] T003 [G1] [P] [US1] Modify `src/friday/memory/dynamic.py`: change Mem0 embedder config model from `"BAAI/bge-m3"` to `"BAAI/bge-small-zh-v1.5"`

---

## Phase 3: User Story 2 — 清理旧数据，验证搜索 (Priority: P2)

**Goal**: 清空旧 ChromaDB 数据，验证新模型下搜索功能正常

**Independent Test**: 启动 Friday，录入一条笔记，搜索该笔记内容

- [X] T004 [G2] [US2] Delete old ChromaDB data: remove `~/.friday-memory/` directory (Mem0 old vectors) and recreate knowledge vector collection in `~/.friday/indexes/chroma/` (or delete and let it auto-recreate)
- [X] T005 [G2] [US2] Delete old bge-m3 model cache: remove `~/.cache/huggingface/hub/models--BAAI--bge-m3/` directory (~2.1 GB)

---

## Phase 4: Polish & 验证

**Purpose**: 端到端验证内存和功能

- [X] T006 [G3] Run `scripts/memory_profile.py` to verify: embedding model memory delta < 200 MB, total RSS < 500 MB
- [X] T007 [G3] Start Friday interactive mode, add a note with "记一下 测试笔记内容", then search for "测试笔记" to verify search works with new model

---

## Parallel Groups

| Group | Tasks | Depends On | Notes |
|-------|-------|------------|-------|
| G0    | T001 | — | Read and confirm, 串行 |
| G1    | T002, T003 | G0 | **并行** — 不同文件 |
| G2    | T004, T005 | G1 | **并行** — 不同目录 |
| G3    | T006, T007 | G2 | **并行** — 独立验证 |

**Max parallelism**: 2 (G1, G2, G3)
**Total groups**: 4
**Total tasks**: 7

---

## Implementation Strategy

### MVP (Phase 1 + Phase 2)

1. T001 → 确认改动点
2. T002 + T003 并行 → 核心代码改完
3. **STOP** → 启动 Friday 验证能正常加载新模型

### Full Delivery

1. MVP 完成
2. T004 + T005 清理旧数据/缓存（释放 ~2.1 GB）
3. T006 + T007 端到端验证
