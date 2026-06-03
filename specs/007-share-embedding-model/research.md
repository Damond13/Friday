# Research: 共享 Embedding 模型实例

**Date**: 2026-06-03
**Feature**: specs/007-share-embedding-model

## 调研问题

### 1. Mem0 内部嵌入模型存放位置

**Decision**: Mem0 的 HuggingFace embedder 将 SentenceTransformer 实例存储在 `self.model` 属性中，通过 `memory_instance.embedding_model.model` 访问。

**Rationale**: 通过阅读 Mem0 源码确认：
- `Memory.from_config(config)` 创建 `Memory` 实例
- 内部 `embedding_model` 是 `HuggingFaceEmbedding` 实例
- `HuggingFaceEmbedding.model` 是 `SentenceTransformer` 实例
- 替换此属性即可让 Mem0 使用外部共享的模型

**Alternatives considered**:
- 继承/子类化 HuggingFaceEmbedding：过于复杂，需修改 Mem0 内部代码
- 自定义 embedder provider：需要实现完整接口，工作量大
- 直接替换属性（选中）：最简单直接，一行代码完成

### 2. 编码参数兼容性

**Decision**: 共享模型实例是安全的。`normalize_embeddings` 和 `convert_to_numpy` 是 `encode()` 的调用时参数，不是模型实例的属性。

**Rationale**:
- knowledge/embedding.py 调用 `model.encode(texts, normalize_embeddings=True)`
- Mem0 内部调用 `model.encode(text, convert_to_numpy=True)`
- 两者互不影响，各自传入自己的参数即可
- `lru_cache` 缓存的是模型实例，不缓存 encode 行为

**Alternatives considered**:
- 担心参数冲突而创建两个实例：不必要，已确认是调用时参数

### 3. 依赖方向和模块边界

**Decision**: 允许 memory/ 从 knowledge/embedding.py 导入 `get_shared_model()`，在 complexity tracking 中记录。

**Rationale**:
- embedding.py 本质是模型 adapter，服务多个消费者是 adapter 的职责
- 此依赖仅为获取模型实例引用，不涉及知识库业务逻辑
- 替代方案（新建公共模块）对小优化来说过度设计

**Alternatives considered**:
- 新建 `src/friday/common/embedding.py`：引入新的目录结构和导入链，过度设计
- 将模型放到 memory/ 中让 knowledge/ 反向依赖：语义不合理，嵌入更偏知识检索概念
- 保持现状各用各的：内存浪费 2GB，不符合"简洁实用"原则

### 4. 错误隔离

**Decision**: 在 `_init_memory()` 中用 try/except 包裹模型注入逻辑，注入失败不影响 Mem0 初始化。

**Rationale**: Mem0 初始化即使不替换模型也能正常工作（会用自己加载的实例）。注入失败只意味着内存没省下来，功能不受影响。

**Alternatives considered**:
- 注入失败时阻止 Mem0 初始化：过于严格，退化行为更好
