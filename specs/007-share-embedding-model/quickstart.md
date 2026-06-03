# Quickstart: 共享 Embedding 模型实例验证

**Feature**: specs/007-share-embedding-model
**Date**: 2026-06-03

## 验证步骤

### 1. 运行全部自动化测试

```bash
uv run pytest tests/ -v
```

预期：260 passed, 2 skipped（Mem0 OpenAI Key 相关），无新增失败。

### 2. 验证知识库功能不受影响

```bash
uv run python -c "
from friday.knowledge.store import KnowledgeStore
store = KnowledgeStore()
store.add_note('测试共享模型', tags=['test'])
results = store.search('共享模型')
print('知识库搜索结果:', results)
"
```

预期：能正确搜索到笔记。

### 3. 验证动态记忆功能不受影响

```bash
uv run python -c "
from friday.memory.dynamic import add_memory, search_memory
add_memory('共享模型实例测试', {'source': 'test'})
results = search_memory('共享模型')
print('动态记忆搜索结果:', [(r.content, r.score) for r in results])
"
```

预期：能正确检索到动态记忆。

### 4. 验证共享实例

```bash
uv run python -c "
from friday.knowledge.embedding import get_shared_model, _get_model
from friday.memory.dynamic import _get_memory

# 知识库的模型实例
kb_model = get_shared_model()

# 触发动态记忆初始化（如已初始化则跳过）
m = _get_memory()
if m is not None:
    mem0_model = m.embedding_model.model
    print('同一个实例:', kb_model is mem0_model)
else:
    print('Mem0 未初始化，无法验证')
"
```

预期：输出 `同一个实例: True`。
