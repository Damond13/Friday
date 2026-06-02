# API Contract: memory 模块公共接口

**Module**: `friday.memory`
**Entry Point**: `adapter.py`

## 公共 API

### add_memory(content, metadata) → MemoryItem

添加一条动态记忆。

**Parameters**:
- `content: str` — 记忆内容
- `metadata: dict | None` — 元数据（session_id, source 等）

**Returns**: `MemoryItem` — 存储后的记忆对象

**Example**:
```python
from friday.memory import add_memory, search_memories

item = add_memory("用户偏好暗色主题", metadata={"source": "chat"})
```

---

### search_memories(query, limit) → list[MemorySearchResult]

统一搜索两层记忆。

**Parameters**:
- `query: str` — 搜索文本
- `limit: int` — 返回最多 N 条结果，默认 10

**Returns**: `list[MemorySearchResult]` — 按评分降序

**Example**:
```python
results = search_memories("颜色偏好")
# [MemorySearchResult(source="dynamic", content="用户偏好暗色主题", score=0.85)]
```

---

### list_memories() → list[MemoryItem]

列出所有动态记忆。

**Returns**: `list[MemoryItem]`

---

### delete_memory(memory_id) → bool

删除指定动态记忆。

**Parameters**:
- `memory_id: str` — 记忆 ID

**Returns**: `bool` — 是否成功

---

### add_decision(title, decision, context, status) → Decision

添加一条决策记录。

**Parameters**:
- `title: str` — 决策标题
- `decision: str` — 决定内容
- `context: str` — 背景
- `status: str` — 状态，默认 "已采纳"

**Returns**: `Decision`

---

### list_decisions() → list[Decision]

列出所有决策记录，按时间倒序。

**Returns**: `list[Decision]`

---

### add_lesson(title, lesson, context) → Lesson

添加一条经验教训。

**Parameters**:
- `title: str` — 经验标题
- `lesson: str` — 经验内容
- `context: str` — 场景描述

**Returns**: `Lesson`

---

### list_lessons() → list[Lesson]

列出所有经验教训，按时间倒序。

**Returns**: `list[Lesson]`

---

### get_constitution() → str

读取项目宪法内容。

**Returns**: `str` — 宪法 Markdown 内容，不存在返回空字符串

## 类型导出

- `MemoryItem` — 动态记忆条目
- `MemorySearchResult` — 统一检索结果
- `Decision` — 决策记录
- `Lesson` — 经验教训
