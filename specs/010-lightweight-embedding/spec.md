# Feature Specification: 轻量 Embedding 模型切换

**Feature Branch**: `010-lightweight-embedding`

**Created**: 2026-06-05

**Status**: Draft

**Input**: User description: "将 Embedding 模型从 bge-m3（2.1GB）切换为 bge-small-zh-v1.5（~100MB），降低 Friday 启动内存占用约 95%，同时重建现有 ChromaDB 向量索引以兼容新模型维度"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 启动后内存大幅降低 (Priority: P1)

作为用户，当我启动 Friday 时，我希望应用的内存占用在合理范围内（几百 MB 而非几 GB），这样我的电脑不会因为运行一个本地助手就变得卡顿。

**Why this priority**: 这是用户直接感知的问题。当前 Friday 启动后活动监视器显示 ~6 GB（含 mmap 映射），导致 macOS 内存压力变黄。这是阻碍正常使用的首要问题。

**Independent Test**: 启动 Friday，在活动监视器中确认内存占用从 ~6 GB 降至 ~300 MB。

**Acceptance Scenarios**:

1. **Given** Friday 使用 bge-m3 模型（2.1 GB 权重文件），**When** 切换为 bge-small-zh-v1.5（~100 MB 权重文件），**Then** 活动监视器显示的内存占用降低至原来的 1/6 以下
2. **Given** 用户启动 Friday，**When** 首次发送消息触发 embedding 加载，**Then** 加载时间不超过 10 秒，且加载后内存增长不超过 200 MB

---

### User Story 2 - 搜索功能正常工作 (Priority: P2)

作为用户，当模型切换后，我希望知识搜索和记忆搜索仍然正常工作，可以重新录入和检索知识。

**Why this priority**: 模型切换后 ChromaDB 向量维度变化，需要清空旧数据并验证新模型下搜索功能正常。

**Independent Test**: 切换后录入一条新笔记，搜索该笔记内容，验证能找到。

**Acceptance Scenarios**:

1. **Given** 模型切换完成且旧 ChromaDB 数据已清空，**When** 用户录入新知识笔记，**Then** 通过搜索能找到该笔记
2. **Given** 模型切换完成，**When** 用户与 Friday 对话产生新的动态记忆，**Then** 记忆搜索能返回结果

---

### Edge Cases

- 新模型首次下载失败（网络问题）时的错误提示
- 旧 ChromaDB 数据清空后 Mem0 首次初始化是否正常

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统必须将 embedding 模型从多语言大模型切换为中文专用轻量模型，模型权重文件大小不超过 150 MB
- **FR-002**: 切换后 Friday 启动并首次加载模型后的内存增量不超过 200 MB（当前为 ~734 MB）
- **FR-003**: 模型配置必须集中管理（单一配置点），知识库和记忆系统使用同一个模型实例
- **FR-004**: 切换后必须清空旧 ChromaDB 向量数据（维度不兼容），确保新模型能正常创建和使用新集合
- **FR-005**: 切换后知识搜索和记忆搜索功能必须正常工作（录入 → 搜索 → 返回结果）
- **FR-006**: 旧模型缓存文件（~2.1 GB）应在确认新模型工作正常后清理，释放磁盘空间

### Key Entities

- **EmbeddingConfig**: 模型配置，包含模型名称、向量维度

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Friday 启动并加载 embedding 模型后，活动监视器显示的内存增量不超过 200 MB（含 mmap 映射）
- **SC-002**: 录入一条知识笔记后搜索该笔记内容，能正确返回结果
- **SC-003**: 模型首次加载时间不超过 10 秒（本地缓存命中时不超过 3 秒）
- **SC-004**: 旧模型缓存文件清理后，磁盘空间释放至少 2 GB

## Assumptions

- bge-small-zh-v1.5 的向量维度为 512（bge-m3 为 1024），旧 ChromaDB 数据无法兼容，直接清空
- 用户确认历史数据（知识笔记向量、动态记忆）可以丢弃，不需要迁移
- bge-small-zh-v1.5 在中文语义搜索场景下的表现足以满足 Friday 的使用需求
- 切换后旧的 bge-m3 缓存可以安全删除以释放磁盘空间
