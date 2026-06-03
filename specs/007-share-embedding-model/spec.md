# Feature Specification: 共享 Embedding 模型实例

**Feature Branch**: `007-share-embedding-model`

**Created**: 2026-06-03

**Status**: Draft

**Input**: 知识库模块和动态记忆模块各自加载 BAAI/bge-m3 模型，占用约 4GB 内存，需要共享同一个实例降至约 2GB

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 模型只加载一次 (Priority: P1)

作为 Friday 的用户，当我同时使用知识库搜索和动态记忆功能时，系统只应加载一次嵌入模型，而不是加载两份副本浪费内存。

**Why this priority**: 这直接影响系统资源占用（4GB → 2GB），是本需求的核心价值

**Independent Test**: 启动 Friday 后同时触发知识库搜索和动态记忆操作，验证内存中只有一个模型实例

**Acceptance Scenarios**:

1. **Given** Friday 系统已启动且模型尚未加载，**When** 用户先后使用知识库搜索和动态记忆功能，**Then** 模型只在首次调用时加载一次，后续调用复用同一实例
2. **Given** 模型已加载到内存，**When** 检查知识库和动态记忆使用的模型实例，**Then** 两者引用的是同一个对象

---

### User Story 2 - 共享后功能不受影响 (Priority: P1)

作为 Friday 的用户，共享模型实例后，知识库搜索（全文 + 语义）和动态记忆（添加/检索/删除）的所有功能应与共享前完全一致。

**Why this priority**: 功能正确性是任何优化的前提，必须保证

**Independent Test**: 运行全部现有测试套件（260 个测试），确保无回归

**Acceptance Scenarios**:

1. **Given** 知识库中已有笔记，**When** 用户执行语义搜索，**Then** 搜索结果与共享前一致
2. **Given** 用户添加一条动态记忆，**When** 用户搜索该记忆内容，**Then** 能够正确检索到
3. **Given** 用户执行知识库 RAG 问答，**Then** 回答质量与共享前一致

---

### Edge Cases

- 当动态记忆（Mem0）初始化失败时，知识库的嵌入功能应不受影响，独立可用
- 知识库使用 `normalize_embeddings=True` 编码，动态记忆使用不同的编码参数，共享实例后各自的编码行为应保持不变
- 模型加载失败时（如文件损坏），应有清晰的错误提示，不应导致整个系统崩溃

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统必须提供获取共享嵌入模型实例的方式，确保全局只有一个模型副本
- **FR-002**: 知识库模块和动态记忆模块必须使用同一个模型实例进行文本向量化
- **FR-003**: 共享模型实例后，知识库的全文搜索、语义搜索和 RAG 问答功能必须保持原有行为
- **FR-004**: 共享模型实例后，动态记忆的添加、检索、列表、删除功能必须保持原有行为
- **FR-005**: 动态记忆初始化失败时，必须不影响知识库模块的独立性
- **FR-006**: 系统必须在模型加载失败时给出明确提示，而不是静默失败

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 系统同时使用知识库和动态记忆功能时，内存中嵌入模型实例数不超过 1 个
- **SC-002**: 现有 260 个自动化测试全部通过，无回归
- **SC-003**: 知识库语义搜索和动态记忆检索的结果质量与改动前一致
- **SC-004**: 模型加载后，动态记忆功能初始化成功率不低于改动前

## Assumptions

- 嵌入模型 BAAI/bge-m3 已下载到本地缓存，无需重新下载
- 知识库和动态记忆的编码参数差异（normalize_embeddings）是调用时参数而非实例属性，共享模型后各自的调用行为不变
- 此优化仅涉及两个模块间的模型实例共享，不改变任何对外接口或数据格式
