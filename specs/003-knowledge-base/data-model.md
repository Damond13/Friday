# 数据模型：知识库模块

**Feature**: 003-knowledge-base | **Date**: 2026-06-02

## 实体定义

### Note（笔记）

一条用户知识的完整记录，以 Markdown 文件形式存储。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | str | 唯一标识，UUID hex[:8] |
| title | str | 笔记标题 |
| content | str | 笔记正文 |
| tags | list[str] | 标签列表 |
| created_at | str | 创建时间，ISO 格式 |
| file_path | Path | 文件存储路径 |

**存储位置**: `~/.friday/knowledge/notes/{id}.md`

**文件格式**:
```markdown
---
id: abc12345
title: Python 装饰器
tags: [python, 编程]
created_at: 2026-06-02T10:30:00
---

Python 装饰器就是函数包装器...
```

### IndexEntry（索引条目）

关联 Note 的索引数据，分别存在于 FTS5 和 ChromaDB 中。

**FTS5 表结构**:
| 字段 | 类型 | 说明 |
|------|------|------|
| note_id | TEXT | 关联 Note.id（主键） |
| title | TEXT | 分词后的标题 |
| content | TEXT | 分词后的正文 |
| tags | TEXT | 空格分隔的标签 |
| file_path | TEXT | 原始文件路径 |

**ChromaDB Collection**:
| 字段 | 说明 |
|------|------|
| id | note_id |
| embedding | bge-m3 生成的 1024 维向量 |
| document | 原始文本内容 |
| metadata | {title, tags, file_path, created_at} |

### SearchResult（检索结果）

检索接口的返回类型。

| 字段 | 类型 | 说明 |
|------|------|------|
| note_id | str | 关联的笔记 ID |
| title | str | 笔记标题 |
| snippet | str | 匹配的内容片段 |
| score | float | 相关度分数（0-1，越高越相关） |
| source | str | 来源：fts / vector / rag |
| file_path | str | 原始文件路径 |

## 实体关系

```
Note (1) ──── (1) FTS5 IndexEntry
  │
  └─────── (1) ChromaDB VectorEntry

Note ──file_path──→ ~/.friday/knowledge/notes/{id}.md
```

每个 Note 在 FTS5 和 ChromaDB 中各有一条对应记录，通过 note_id 关联。

## 状态流转

```
[创建] → 录入笔记 → 写入文件 → 建立索引（FTS5 + ChromaDB）
[修改] → 文件变化 → 检测到变化 → 增量更新索引
[删除] → 删除文件 → 检测到变化 → 移除索引条目
```
