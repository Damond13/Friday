# Data Model: 双层记忆系统

**Date**: 2026-06-02 | **Branch**: `006-dual-layer-memory`

## Entities

### MemoryItem

动态记忆条目，由 Mem0 存储和管理。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | str | 是 | Mem0 分配的唯一标识 |
| content | str | 是 | 记忆内容文本 |
| metadata | dict | 否 | 元数据（source, created_at 等） |
| score | float | 否 | 检索相关度评分（0.0~1.0） |

**来源**: 由 Mem0 的 add/search/get_all API 返回

### Decision

决策记录条目。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | str | 是 | 决策标题 |
| date | str | 是 | ISO 日期 |
| status | str | 是 | 已提议/已采纳/已废弃 |
| context | str | 否 | 决策背景 |
| decision | str | 是 | 决定内容 |

**存储**: `decisions.md` 文件中，按时间倒序

### Lesson

经验教训条目。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | str | 是 | 经验标题 |
| date | str | 是 | ISO 日期 |
| context | str | 否 | 发生场景 |
| lesson | str | 是 | 经验内容 |

**存储**: `lessons-learned.md` 文件中，按时间倒序

### MemorySearchResult

统一检索返回值。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| source | str | 是 | 来源："dynamic" / "files" |
| content | str | 是 | 记忆内容 |
| score | float | 是 | 相关度评分 0.0~1.0 |
| metadata | dict | 否 | 额外元数据 |

## Storage Mapping

### 动态记忆（Mem0 ChromaDB）

```
.friday-memory/
├── chroma.sqlite3           # ChromaDB 数据文件
└── ...                      # ChromaDB 内部文件
```

### 结构化文件记忆

```
.specify/memory/
├── constitution.md          # 项目宪法（已有）
├── decisions.md             # 决策记录
└── lessons-learned.md       # 经验教训
```
