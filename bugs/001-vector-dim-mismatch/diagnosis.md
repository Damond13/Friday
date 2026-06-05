# 根因诊断: 知识库向量检索维度不匹配

**日期**: 2026-06-06 | **缺陷来源**: bug-report.md

## 根因分析

### 直接原因

`vector.py:32` 使用 `get_or_create_collection` 获取已有的 `friday_notes` 集合。该集合在 bge-m3 时代以 1024 维创建，现在 bge-small-zh 产出 512 维向量，`collection.query()` 触发维度不匹配异常。

调用链：
- `adapter.py:82` `vector.search()` → `vector.py:73` `embed_text()`（512维）→ `vector.py:74` `collection.query()` → ChromaDB 拒绝（期望1024维）
- 异常被 `adapter.py:84` 捕获，降级为 FTS5

### 根本原因

两层遗漏：

1. **spec 010 执行遗漏** — T004 只清了 Mem0 的 `~/.friday-memory/`，没清知识库的 `~/.friday/knowledge/chroma/`（672KB 测试数据）
2. **设计缺陷** — `_get_collection()`（`vector.py:29-35`）没有校验现有 collection 的维度是否和当前 embedding 模型匹配。ChromaDB 的 `get_or_create_collection` 不会在获取时校验维度，只在查询/插入时才报错。未来再换模型会再次触发同样问题

## 调研发现

### 开源社区同类问题

ChromaDB 维度不匹配是已知常见问题，多个项目遇到过：
- [CrewAI #2464](https://github.com/crewAIInc/crewAI/issues/2464) — 换 embedding 模型后需要 reset memory
- [ChromaDB #4368](https://github.com/chroma-core/chroma/issues/4368) — InvalidDimensionException
- [StackOverflow](https://stackoverflow.com/questions/77694864/invaliddimensionexception-embedding-dimension-384-does-not-match-collection-dim) — 旧 collection 维度和新模型不一致

### 社区标准解法

| 方案 | 描述 |
|------|------|
| 删除旧 collection 重建 | 最常见的解法，切换模型时必须重建 |
| 校验维度后再操作 | 在代码中主动检查 collection 维度和模型维度是否一致 |
| ChromaDB 不校验 | `get_or_create_collection` 不做维度校验，只在 query/insert 时报错 |

## 问题分级

- [x] **代码级 bug** — 向量存储方案正确，只是缺少维度校验 + 旧数据未清理 → 进入 fixplan
- [ ] **方案级问题**

## 诊断结论

旧 ChromaDB 集合未清理（1024维）+ 代码缺少维度校验，导致新模型（512维）查询时维度不匹配。需要清理旧数据，并在代码中加入维度校验防止未来再发。
