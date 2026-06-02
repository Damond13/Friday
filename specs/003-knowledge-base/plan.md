# 实现计划：知识库模块

**Branch**: `003-knowledge-base` | **Date**: 2026-06-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-knowledge-base/spec.md`

## 概要

知识库模块提供个人知识的存储、三层递进检索（FTS5 → ChromaDB → RAG）和自动文件监控索引。使用 ChromaDB 存储向量、SQLite FTS5 做全文搜索、watchdog 做文件监控，本地 `BAAI/bge-m3` 模型做 embedding（不调 API，不花 token）。

## 技术上下文

**Language/Version**: Python 3.13

**Primary Dependencies**: chromadb, watchdog, sentence-transformers

**Storage**: SQLite FTS5（全文索引）+ ChromaDB PersistentClient（向量索引）+ Markdown 文件（笔记原文）

**Testing**: pytest

**Target Platform**: 本地 CLI（macOS / Linux）

**Project Type**: CLI 工具

**Performance Goals**: FTS5 < 100ms, ChromaDB < 500ms, RAG < 3s

**Constraints**: 全部本地运行，不依赖外部 API 做 embedding

**Scale/Scope**: 万条以内知识

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原则 | 状态 | 说明 |
|------|------|------|
| I. 个人化优先 | PASS | 个人知识库，用户独享 |
| II. 渐进式学习 | PASS | 对话式录入"记一下 xxx" |
| III. 本地优先 | PASS | 全部存储在 ~/.friday/，embedding 用本地模型 |
| IV. 安全可控 | PASS | 只读/写用户自己的知识目录 |
| V. 简洁实用 | PASS | CLI 操作，三层检索按需递进 |
| 编码规范 | PASS | 文件 < 200 行，函数 < 30 行，adapter 层 |
| 模块边界 | PASS | knowledge/ 只管知识存取和检索，不关心展示 |

## Project Structure

### Documentation (this feature)

```text
specs/003-knowledge-base/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── knowledge-api.md
└── tasks.md
```

### Source Code (repository root)

```text
src/friday/knowledge/
├── __init__.py          # 公共 API 导出
├── adapter.py           # 统一检索接口（上层调用入口）
├── store.py             # 笔记文件管理（创建/删除/列表）
├── fts.py               # FTS5 全文索引管理
├── vector.py            # ChromaDB 向量索引管理
├── watcher.py           # watchdog 文件监控 + 增量索引
└── embedding.py         # 本地 embedding（bge-m3 adapter）

tests/
├── unit/
│   ├── test_store.py
│   ├── test_fts.py
│   ├── test_vector.py
│   └── test_adapter.py
└── conftest.py
```

**Structure Decision**: 单项目结构，knowledge/ 作为独立模块，通过 adapter.py 对外暴露统一接口。

## Complexity Tracking

无宪法违规，无需记录。
