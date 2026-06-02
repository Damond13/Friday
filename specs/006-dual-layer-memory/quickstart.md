# Quickstart: 双层记忆系统验证场景

**Date**: 2026-06-02 | **Branch**: `006-dual-layer-memory`

## 场景 1: 添加和检索动态记忆

```python
from friday.memory import add_memory, search_memories, delete_memory

# 添加记忆
item = add_memory("用户偏好暗色主题和 Vim 编辑器")
assert item.content != ""
assert item.id != ""

# 语义检索
results = search_memories("编辑器偏好")
assert len(results) >= 1
assert any("Vim" in r.content or "编辑器" in r.content for r in results)

# 删除
deleted = delete_memory(item.id)
assert deleted is True
```

## 场景 2: 列出所有动态记忆

```python
from friday.memory import add_memory, list_memories

add_memory("用户使用 Python 3.13 开发")
add_memory("项目名称是 Friday")

all_items = list_memories()
assert len(all_items) >= 2
```

## 场景 3: 添加和列出决策记录

```python
from friday.memory import add_decision, list_decisions

decision = add_decision(
    title="使用 adapter 模式隔离第三方依赖",
    decision="所有外部 SDK 调用走 adapter 层",
    context="需要隔离 LLM provider 变更的影响",
)
assert decision.title != ""

decisions = list_decisions()
assert len(decisions) >= 1
assert decisions[0].title == "使用 adapter 模式隔离第三方依赖"
```

## 场景 4: 添加和列出经验教训

```python
from friday.memory import add_lesson, list_lessons

lesson = add_lesson(
    title="SQLite WAL 模式避免锁竞争",
    lesson="多进程写入场景必须用 WAL 模式",
    context="executor 模块开发中遇到的数据库锁定问题",
)
assert lesson.title != ""

lessons = list_lessons()
assert len(lessons) >= 1
```

## 场景 5: 统一检索跨两层

```python
from friday.memory import add_memory, add_decision, search_memories

add_memory("项目使用 Mem0 管理动态记忆")
add_decision("选择 Mem0 而非自建", "使用 Mem0 封装记忆管理", "减少开发量")

results = search_memories("记忆管理方案")
# 应包含动态记忆和/或文件记忆的结果
assert len(results) >= 1
```
