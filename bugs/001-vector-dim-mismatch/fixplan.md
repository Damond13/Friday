# 修复方案: 知识库向量检索维度不匹配

**日期**: 2026-06-06 | **缺陷来源**: bug-report.md | **诊断依据**: diagnosis.md

## 修复策略

在向量集合获取时加入维度校验，检测到 embedding 维度变化时自动删除旧集合并重建。覆盖知识库和 Mem0 两个 ChromaDB 实例。

## 长期影响评估

### 可扩展性

正面。collection metadata 中记录 embedding_dim，未来换模型时自动检测和处理，无需手动清理。

### 未来功能影响

正面。如果后续支持多 embedding 模型切换，维度校验是基础能力。

### 风险

- 旧向量数据会丢失（但维度不匹配的旧数据本身已无法使用，丢失无影响）
- Mem0 probe 搜索增加一次初始化开销（可忽略）

## 改动清单

| 文件 | 改动内容 | 原因 |
|------|---------|------|
| `src/friday/knowledge/vector.py:29-35` | `_get_collection()` 增加 `embedding_dim` metadata 记录和校验，不匹配时 delete + recreate | 知识库维度校验，根治维度不匹配问题 |
| `src/friday/memory/dynamic.py` `_init_memory()` | 初始化后做一次 probe 搜索，维度不匹配时清理 `MEMORY_DIR` 并重试 | Mem0 维度校验（防御性） |

## 不改动的部分

- `embedding.py` — 模型配置正确，不改
- `adapter.py` — 降级逻辑是合理的防御机制，保留
- `store.py`、`fts.py` — 无关
- `~/.friday/knowledge/chroma/` 目录 — 不手动删除，由代码自动检测并重建

## 验证方案

1. 启动 Friday，搜索任意内容，确认不再出现"向量检索失败"
2. 添加一条新笔记，确认向量索引正常
3. 搜索该笔记内容，确认语义检索返回结果
