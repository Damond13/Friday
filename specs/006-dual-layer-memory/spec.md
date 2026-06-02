# Feature Specification: 双层记忆系统

**Feature Branch**: `006-dual-layer-memory`

**Created**: 2026-06-02

**Status**: Draft

**Input**: User description: "双层记忆系统"

## User Scenarios & Testing

### User Story 1 - 动态记忆存取 (Priority: P1)

Friday 在对话中自动提取关键信息并存储为动态记忆。用户可以通过关键词或语义检索找回相关记忆。

**Why this priority**: 动态记忆是 Friday 个人化的核心能力，没有记忆就无法"记住"用户。

**Independent Test**: 添加一条记忆"用户偏好暗色主题"，通过语义搜索"颜色偏好"能检索到该记忆。

**Acceptance Scenarios**:

1. **Given** 一条对话片段"我喜欢用 Vim 写代码"，**When** 系统提取并存储记忆，**Then** 记忆被保存，可通过"编辑器"关键词检索到
2. **Given** 已存储多条记忆，**When** 用户搜索相关主题，**Then** 返回按相关度排序的记忆列表
3. **Given** 一条不再需要的记忆，**When** 用户删除它，**Then** 后续搜索不再返回

---

### User Story 2 - 结构化文件记忆 (Priority: P2)

用户可以管理结构化的文件记忆：宪法（constitution）、决策记录（decisions）、经验教训（lessons-learned）。这些文件支持直接编辑和 Git 版本管理。

**Why this priority**: 结构化记忆提供稳定的项目级知识，但动态记忆的即时价值更高。

**Independent Test**: 写入一条决策记录，读取后内容一致。

**Acceptance Scenarios**:

1. **Given** 用户想记录一条架构决策，**When** 添加决策记录，**Then** 文件被更新，包含时间戳和内容
2. **Given** 已存在 3 条决策记录，**When** 用户列出所有决策，**Then** 返回按时间倒序的完整列表
3. **Given** 用户修改经验教训文件，**When** 重新读取，**Then** 返回更新后的内容

---

### User Story 3 - 统一记忆检索 (Priority: P3)

LLM 调用层需要从两个记忆层获取相关上下文。memory 模块提供统一检索接口，同时搜索动态记忆和结构化文件记忆。

**Why this priority**: 统一检索是 LLM prompt 组装的前置条件，但各层独立可用即可满足基本需求。

**Independent Test**: 存入动态记忆和文件记忆各一条，统一搜索返回两层的结果。

**Acceptance Scenarios**:

1. **Given** 动态记忆中有"喜欢 Vim"，文件记忆中有"项目使用 Python 3.13"，**When** 搜索"开发环境"，**Then** 两条记忆都出现在结果中
2. **Given** 仅动态记忆有匹配，**When** 搜索，**Then** 返回动态记忆结果，文件记忆部分为空
3. **Given** 搜索无匹配，**When** 搜索，**Then** 返回空结果

---

### Edge Cases

- 动态记忆存储服务不可用时：返回降级结果（仅文件记忆），记录警告
- 结构化文件被手动删除时：返回空内容而非报错
- 记忆内容过长时：动态记忆自动截断，文件记忆按原样存储
- 搜索查询为空时：返回空结果

## Requirements

### Functional Requirements

- **FR-001**: 系统必须支持添加动态记忆（文本内容 + 元数据）
- **FR-002**: 系统必须支持语义检索动态记忆（输入文本，返回相关记忆列表）
- **FR-003**: 系统必须支持删除指定动态记忆
- **FR-004**: 系统必须支持列出所有动态记忆（分页）
- **FR-005**: 系统必须支持管理结构化文件记忆：宪法、决策记录、经验教训
- **FR-006**: 结构化文件记忆必须以 Markdown 格式存储，便于人工编辑
- **FR-007**: 系统必须提供统一检索接口，同时搜索动态和文件记忆
- **FR-008**: 所有记忆数据必须存储在本地，不依赖云服务
- **FR-009**: 动态记忆存储目录为 `.friday-memory/`，文件记忆存储目录为 `.specify/memory/`

### Key Entities

- **动态记忆 (Memory)**: 从对话中提取的关键信息片段。包含内容、元数据（来源、时间）、唯一标识
- **决策记录 (Decision)**: 结构化文件记忆条目。包含标题、内容、时间戳、分类标签
- **经验教训 (Lesson)**: 从开发过程中总结的经验。包含内容、上下文、时间戳
- **检索结果 (SearchResult)**: 统一检索的返回值。包含来源类型（动态/文件）、内容、相关度评分

## Success Criteria

### Measurable Outcomes

- **SC-001**: 动态记忆添加和检索操作在 500 毫秒内完成
- **SC-002**: 语义检索在前 5 条结果中包含相关记忆的比率达到 80% 以上
- **SC-003**: 结构化文件记忆可直接用文本编辑器打开和修改
- **SC-004**: 统一检索接口在一次调用中返回两层记忆结果
- **SC-005**: 所有记忆数据完全存储在本地文件系统中

## Assumptions

- 动态记忆的自动提取由 LLM 调用层负责，memory 模块只接收提取后的结构化数据并存储
- Mem0 库负责动态记忆的向量化存储和语义检索
- 结构化文件记忆使用固定的文件名：constitution.md、decisions.md、lessons-learned.md
- 决策记录和经验教训按时间倒序追加到文件末尾
- MVP 阶段动态记忆的元数据仅包含来源会话 ID 和时间戳
