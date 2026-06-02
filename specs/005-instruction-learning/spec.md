# Feature Specification: 指令学习模块

**Feature Branch**: `005-instruction-learning`

**Created**: 2026-06-02

**Status**: Draft

**Input**: User description: "指令学习模块"

## User Scenarios & Testing

### User Story 1 - 对话式教学 (Priority: P1)

用户通过自然语言教会 Friday 一条新指令。例如："以后每次我说'部署'，你就执行 `./deploy.sh`"。Friday 将触发词和对应动作以 YAML 格式保存。

**Why this priority**: 教学是核心入口，没有教学就没有指令可匹配。这是 MVP 必须具备的能力。

**Independent Test**: 用户输入一条教学语句，系统解析出触发词和动作，成功保存为 YAML 文件并可通过加载验证。

**Acceptance Scenarios**:

1. **Given** 用户说"以后每次我说'deploy'，你就执行 `./deploy.sh`"，**When** 系统解析这句话，**Then** 创建一条指令：触发词"deploy"，动作"执行 `./deploy.sh`"，类型为单步指令
2. **Given** 用户说"帮我记住：检查磁盘空间就用 `df -h`"，**When** 系统解析这句话，**Then** 创建一条指令：触发关键词"检查磁盘空间"，动作"执行 `df -h`"
3. **Given** 触发词与已有指令重复，**When** 系统保存，**Then** 提示用户是否覆盖已有指令

---

### User Story 2 - 指令匹配 (Priority: P2)

用户在对话中说出与已学指令匹配的内容，Friday 识别出匹配的指令并返回匹配结果（指令内容），供 LLM 调用层决策执行。

**Why this priority**: 匹配是指令系统的核心能力，但依赖教学（US1）先有数据。

**Independent Test**: 预存若干指令后，输入匹配文本，系统能正确返回最佳匹配。

**Acceptance Scenarios**:

1. **Given** 已存在指令"deploy → 执行 ./deploy.sh"，**When** 用户输入"帮我 deploy 一下"，**Then** 系统返回匹配到该指令，匹配度标注为高
2. **Given** 已存在指令"检查磁盘 → 执行 df -h"，**When** 用户输入"看看磁盘"，**Then** 系统通过语义匹配返回该指令
3. **Given** 用户输入不匹配任何指令，**When** 系统查询，**Then** 返回空结果
4. **Given** 多条指令部分匹配，**When** 系统查询，**Then** 按匹配度排序返回

---

### User Story 3 - 指令管理 (Priority: P3)

用户可以查看、编辑、删除已学的指令列表，直接操作 YAML 文件或通过命令管理。

**Why this priority**: 管理能力是长期使用的保障，但核心教学和匹配更重要。

**Independent Test**: 创建若干指令后，通过列表/编辑/删除操作验证指令集合正确变更。

**Acceptance Scenarios**:

1. **Given** 已存在 5 条指令，**When** 用户请求查看所有指令，**Then** 返回按名称排序的完整列表
2. **Given** 已存在指令"deploy"，**When** 用户删除该指令，**Then** 指令被移除，后续匹配不再返回
3. **Given** 用户编辑 YAML 文件修改指令内容，**When** 系统重新加载，**Then** 新内容生效

---

### User Story 4 - 多步工作流 (Priority: P4)

用户可以教会 Friday 一个包含多个步骤的工作流指令，例如："每次我说'发版'，先跑测试、再构建、最后部署"。

**Why this priority**: 扩展能力，单步指令（US1）已满足基本需求。

**Independent Test**: 教学一个多步工作流，触发后返回有序步骤列表。

**Acceptance Scenarios**:

1. **Given** 用户说"每次我说'发版'，先执行 `pytest`，再执行 `build.sh`，最后执行 `deploy.sh`"，**When** 系统解析，**Then** 创建一条多步指令，包含 3 个有序步骤
2. **Given** 存在多步指令"发版"，**When** 用户触发该指令，**Then** 系统返回有序步骤列表供执行层逐步执行
3. **Given** 多步指令中某步骤执行失败，**When** 执行层报告失败，**Then** 后续步骤标记为待确认

---

### Edge Cases

- 触发词为空或过短（少于 2 个字符）时：拒绝保存，提示用户补充
- YAML 文件被手动破坏（语法错误）时：加载时跳过错误文件，记录警告日志
- 指令数量超过一定规模时匹配性能：采用关键词预筛选 + 语义匹配二级策略
- 两条指令触发词完全相同时：后保存的覆盖先保存的，记录覆盖日志

## Requirements

### Functional Requirements

- **FR-001**: 系统必须支持从结构化数据中创建指令（触发词 + 动作列表）
- **FR-002**: 指令必须以 YAML 格式存储在本地文件系统中，每个指令一个文件
- **FR-003**: 系统必须支持三种指令类型：单步指令、多步工作流、条件分支
- **FR-004**: 系统必须提供指令匹配接口，输入文本后返回匹配到的指令列表（按匹配度排序）
- **FR-005**: 系统必须支持指令的增删改查操作
- **FR-006**: 触发词匹配必须同时支持精确匹配和模糊关键词匹配
- **FR-007**: 多步工作流必须维护步骤的执行顺序，支持顺序执行语义
- **FR-008**: 系统必须在加载时自动扫描所有指令文件，跳过格式错误的文件
- **FR-009**: 指令存储目录必须为 `~/.friday/instructions/`
- **FR-010**: 系统必须支持通过修改 YAML 文件直接编辑指令，下次加载时生效

### Key Entities

- **指令 (Instruction)**: 一条用户教会 Friday 的操作规则。包含触发词（trigger）、动作列表（actions）、指令类型（type: single/workflow/conditional）、创建时间、描述等属性
- **动作 (Action)**: 指令中的单个操作步骤。包含执行内容（command）、可选的描述、是否需要确认等属性
- **匹配结果 (MatchResult)**: 指令匹配的返回值。包含匹配到的指令、匹配度评分、匹配类型（精确/关键词）

## Success Criteria

### Measurable Outcomes

- **SC-001**: 用户通过一句话即可教会 Friday 一条新指令，教学过程不超过 1 次交互
- **SC-002**: 精确触发词匹配准确率达到 100%
- **SC-003**: 关键词匹配在前 3 条结果中包含正确指令的比率达到 80% 以上
- **SC-004**: 指令加载和匹配响应时间不超过 100 毫秒（50 条指令以内）
- **SC-005**: YAML 文件可直接用文本编辑器打开和修改，修改后无需重启即可生效

## Assumptions

- 指令匹配使用关键词匹配（精确 + TF 模糊），不依赖向量检索（向量检索由 knowledge 模块负责）
- 条件分支指令在 MVP 阶段简化为步骤描述，具体分支逻辑由 LLM 层在执行时动态解析
- 指令解析（从自然语言提取触发词和动作）由 LLM 层负责，instruction 模块只接收结构化数据并存储
- 指令文件命名规则：使用触发词的拼音或英文作为文件名，如 `deploy.yaml`、`check-disk.yaml`
- 单条指令文件不超过 100 行，保持人工可编辑性
