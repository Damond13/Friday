# Feature Specification: SDD 并行实现

**Feature Branch**: `009-parallel-implement`

**Created**: 2026-06-04

**Status**: Draft

**Input**: User description: "改造SDD工作流本身，支持并行实现，也就是spec.task阶段，拆分可并行的任务，然后在spec.implement阶段拆分agent实现"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 任务阶段识别并行组 (Priority: P1)

作为开发者，当我在 tasks 阶段拆解一个中等以上复杂度的功能时，我希望工作流能自动识别哪些任务之间没有依赖、可以并行执行，并将它们标记为并行组，这样后续实现阶段可以利用多个 Agent 并发处理，缩短整体开发时间。

**Why this priority**: 这是整个功能的基础。没有并行组识别，后续的并行实现无从谈起。当前 tasks.md 已有 `[P]` 标记，但缺乏"并行组"的概念——任务之间谁是同组可并行的、哪些组之间有先后依赖，这些信息没有结构化表达。

**Independent Test**: 可以通过一个示例 spec（如之前 008-agent-tool-loop 的 spec）重新跑 tasks 阶段，验证产出的 tasks.md 中包含清晰的并行组定义和依赖关系图，单独验证这一步就能确认价值。

**Acceptance Scenarios**:

1. **Given** 一个包含 3 个用户故事的 spec 和对应的 plan，**When** 运行 `/speckit.tasks`，**Then** 产出的 tasks.md 中每个任务带有 `group` 标记，同组任务可并行，不同组之间有明确的 `depends_on` 依赖
2. **Given** tasks.md 中有 Phase 2 Foundational 任务和 Phase 3+ 用户故事任务，**When** 分析依赖关系，**Then** Foundational 任务属于 group 0（必须先完成），每个用户故事的任务属于各自的并行组
3. **Given** 同一并行组内的多个任务，**When** 检查文件路径，**Then** 同组任务不修改同一个文件（否则不应标记为可并行）

---

### User Story 2 - 实现阶段编排器调度并行 Agent (Priority: P2)

作为开发者，当我在 implement 阶段执行一个包含并行组的 tasks.md 时，我希望主 Agent 作为编排器，将同组内的可并行任务分别分发给独立的子 Agent（在 git worktree 中隔离执行），等待同组全部完成后合并结果，再进入下一组，这样实现速度能大幅提升。

**Why this priority**: 这是并行执行的核心价值点。没有实际的 Agent 分发和 worktree 隔离，并行标记就只是文档。但这依赖 P1 的并行组定义，所以排在第二。

**Independent Test**: 可以构造一个简单的 tasks.md（如 3 个并行任务 + 1 个串行任务），运行 `/speckit.implement`，观察是否确实启动了多个子 Agent 并发执行，最终所有任务完成且代码合并到功能分支。

**Acceptance Scenarios**:

1. **Given** tasks.md 中 group 1 包含 T005、T006、T007 三个可并行任务，**When** 运行 `/speckit.implement`，**Then** 主 Agent 为这 3 个任务分别创建 worktree 并启动 3 个子 Agent 并发执行
2. **Given** group 1 的 3 个并行任务正在执行中，**When** 其中一个子 Agent 完成，**Then** 主 Agent 不立即合并，而是等待同组全部完成后再统一合并
3. **Given** group 1 完成并合并后，**When** 进入 group 2（依赖 group 1），**Then** group 2 的任务在合并后的代码基础上执行，能看到 group 1 的产出
4. **Given** 某个并行任务执行失败，**When** 同组其他任务已完成，**Then** 主 Agent 报告失败任务，不自动跳过，由用户决定是否重试或跳过

---

### User Story 3 - 开发者可控的并行策略 (Priority: P3)

作为开发者，我希望能控制并行执行的策略（并发数量、是否启用并行、哪些任务强制串行），这样在资源有限或任务间存在隐式依赖时，我可以灵活调整，而不是被强制并行。

**Why this priority**: 可控性是实用性的保障。默认行为应该是安全的，但开发者需要逃生通道。这是对 P2 的增强，不影响核心功能。

**Independent Test**: 可以在 tasks.md 中添加 `strategy` 注解，或在运行 implement 时传入参数，验证策略是否被正确应用（如限制最大并发数、禁用某个任务的并行等）。

**Acceptance Scenarios**:

1. **Given** tasks.md 中有 5 个可并行任务，**When** 开发者设置最大并发数为 2，**Then** 主 Agent 分批执行：先 2 个并发，完成后启动下一批 2 个，最后 1 个
2. **Given** 开发者在 tasks.md 中将某个 `[P]` 任务标记为 `force_sequential`，**When** 运行 implement，**Then** 该任务从并行组中移除，改为串行执行
3. **Given** 开发者运行 `/speckit.implement --no-parallel`，**When** 即使 tasks.md 中有并行组标记，**Then** 所有任务按顺序串行执行（兼容旧工作流）

---

### Edge Cases

- 当两个并行任务需要创建同一个新文件时怎么处理？（tasks 阶段应检测并拆分到不同组）
- 并行任务执行过程中主 Agent 的上下文窗口不够怎么办？（子 Agent 应携带最小必要上下文）
- worktree 创建失败（磁盘空间、git 锁）时的降级策略？
- 所有任务都无法并行（全串行）时，行为应与当前 implement 完全一致

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: tasks 阶段必须为每个任务分配 `group` 编号，同 group 内的任务无文件冲突和依赖关系，可安全并行
- **FR-002**: tasks 阶段必须生成依赖关系图，清晰标注哪些 group 依赖哪些前置 group
- **FR-003**: tasks 阶段必须验证同 group 内的任务不修改同一个文件，冲突的任务应分到不同 group 或标记为串行
- **FR-004**: implement 阶段的主 Agent 必须作为编排器（orchestrator），自身不做具体编码，只负责解析任务、分发、合并
- **FR-005**: implement 阶段必须通过 Claude Code 的 `Agent(..., isolation="worktree")` 为每个并行任务启动独立子 Agent，隔离由 Claude Code 原生管理
- **FR-006**: implement 阶段必须等待同一并行组的所有任务完成后，再统一合并到功能分支
- **FR-007**: implement 阶段必须支持用户配置最大并发数和强制串行选项
- **FR-008**: implement 阶段在子 Agent 失败时必须暂停并报告，由用户决定后续操作
- **FR-009**: 当 tasks.md 中无并行组或用户指定 `--no-parallel` 时，implement 行为必须与当前单 Agent 串行模式完全一致（向后兼容）

### Key Entities

- **ParallelGroup**: 并行组，包含一组无依赖的任务，附带 group 编号和 depends_on 列表
- **TaskContext**: 子 Agent 执行上下文，包含任务描述、相关 plan/spec 摘要、文件路径、worktree 位置
- **OrchestrationPlan**: 编排计划，描述并行组执行顺序、并发限制、降级策略

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 对于包含 3 个以上可并行任务的 spec，implement 阶段的实际执行时间比串行模式减少至少 30%
- **SC-002**: 并行实现产出的代码与串行实现产出的代码功能完全一致，通过相同的测试用例验证
- **SC-003**: 开发者可以在 5 分钟内理解并行任务编排的状态（哪些在执行、哪些完成、哪些失败）
- **SC-004**: 不使用并行功能时（全串行 spec 或 `--no-parallel`），整个工作流行为与改造前完全一致，零回归

## Assumptions

- 开发者使用 git 作为版本控制，Claude Code 原生支持 `isolation: "worktree"` 的 Agent 并发调度，worktree 的创建、合并、清理由 Claude Code 自行管理，SDD 命令不直接操作 worktree
- SDD 命令本质是 markdown 指令文件（`.claude/commands/`），改造范围限于 tasks 和 implement 两个命令的编排逻辑，不涉及 Python 代码
- 同一功能分支上的并行任务不会产生数据库或外部服务的副作用冲突
- 当前 `.claude/commands/speckit.tasks.md` 和 `speckit.implement.md` 是本次改造的直接目标文件
- 项目磁盘空间足够支持多个 worktree 并存（通常每个 worktree 占用等同于主仓库的空间）
