---
name: rag-knowledge
description: RAG 知识库实现参考 — 三层检索架构
---

# RAG 知识库

## 三层检索架构

| 层 | 技术 | 用途 |
|---|---|---|
| 关键词索引 | SQLite FTS5 | 精确匹配，快速定位 |
| 语义索引 | ChromaDB (向量) | 模糊语义，概念匹配 |
| RAG 问答 | LLM + 检索结果 | 综合推理生成回答 |

## 检索策略
- 简单关键词查询 → 走 FTS5（快、准、便宜）
- 模糊描述/概念查询 → 走 ChromaDB（语义匹配）
- 复杂问题 → RAG（检索 + LLM 生成）
- 中文文本入 FTS5 前必须经过 jieba 分词

## ChromaDB 使用要点
- collection 命名只能用 a-z 0-9 _ -，中文标题必须 slug 化
- embedding 模型：本地用 sentence-transformers，或调 API
- 持久化路径：项目下 .friday-memory/

## FTS5 使用要点
- 创建虚拟表：`CREATE VIRTUAL TABLE ft USING fts5(title, content, tokenize='unicode61')`
- 中文需要 jieba 分词后以空格分隔存入
- 支持 BM25 排序
