# Research: 轻量 Embedding 模型切换

**Date**: 2026-06-05 | **Feature**: 010-lightweight-embedding

## 调研 1: bge-small-zh-v1.5 模型规格

**Decision**: 使用 BAAI/bge-small-zh-v1.5

**Rationale**: 同为 BAAI 出品，API 兼容，~100MB，512维，中文专用。Friday 是中文助手，不需要 bge-m3 的多语言能力。

**Alternatives considered**:
1. **bge-base-zh-v1.5** (~400MB) — 精度更高但仍然较大
2. **API embedding** — 零本地内存但需网络，用户未选择此方案

## 调研 2: 旧数据处理

**Decision**: 直接清空旧 ChromaDB 数据，不迁移

**Rationale**: 用户确认历史数据可丢弃。bge-m3（1024维）和 bge-small-zh（512维）维度不兼容，迁移成本高。清空后 ChromaDB 会在下次使用时自动创建新集合。

## 调研 3: 改动点分析

**Decision**: 只需改 2 个文件共 3 行代码

**Rationale**:
- `embedding.py`：改 `_MODEL_NAME` 和 `_EMBEDDING_DIM`（2行）
- `dynamic.py`：改 Mem0 config 中的 model 名称（1行）
- 两处改动后，新模型首次下载到 HuggingFace 缓存，后续使用本地缓存
