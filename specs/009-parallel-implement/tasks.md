# Tasks: SDD 并行实现

**Input**: Design documents from `/specs/009-parallel-implement/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, contracts/task-format.md

**Organization**: Tasks grouped by user story. 本功能的特殊性：改造目标是 2 个 markdown 命令文件，US1 和 US2 分别修改不同文件，因此可以并行执行。

## Format: `[ID] [G{n}] [P?] [Story] Description`

- **[G{n}]**: Parallel Group 编号（G0=串行基础, G1+=可并行组）
- **[P]**: 可并行标记（不同文件，无依赖）
- **[Story]**: US1=任务阶段, US2=实现阶段, US3=策略控制

---

## Phase 1: Setup (共享基础设施)

**Purpose**: 理解现有命令文件结构，确认契约完整

- [X] T001 [G0] Read and analyze current `.claude/commands/speckit.tasks.md` and `.claude/commands/speckit.implement.md`, identify modification points for parallel support
- [X] T002 [G0] Review `specs/009-parallel-implement/contracts/task-format.md` and ensure the [G{n}] marker format and Parallel Groups table contract is finalized

---

## Phase 2: User Story 1 & 2 — 并行组识别 + 编排器调度 (Priority: P1+P2) 🎯 MVP

**Purpose**: US1（tasks 命令）和 US2（implement 命令）修改不同文件，可并行执行

**Goal**: tasks 命令输出带 [G{n}] 标记的并行组任务；implement 命令以编排器模式调度并行子 Agent

**Independent Test**: 用一个示例 spec 运行完整 tasks → implement 流程，验证并行 Agent 确实被启动

### US1 — Tasks 命令并行组识别

- [X] T003 [G1] [P] [US1] Modify `.claude/commands/speckit.tasks.md`: add parallel group detection logic (analyze file paths in task descriptions for conflicts, group independent tasks into [G{n}] markers), update Task Generation Rules section to include [G{n}] format, add `## Parallel Groups` summary table generation at end of output

### US2 — Implement 命令编排器模式

- [X] T004 [G1] [P] [US2] Modify `.claude/commands/speckit.implement.md`: rewrite execution logic as orchestrator — parse tasks.md for [G{n}] markers and Parallel Groups table, for each parallel group launch multiple Agent tool calls with `isolation: "worktree"` in a single message, wait for group completion before proceeding to next group, handle sub-agent failure by pausing and reporting to user, pass minimal context (task description + file paths + relevant plan excerpt) to each sub-agent

**Checkpoint**: US1 和 US2 完成后，完整的并行工作流应该可用。用现有 spec（如 008-agent-tool-loop）测试 tasks 输出是否包含并行组标记，然后测试 implement 是否正确调度。

---

## Phase 3: User Story 3 — 可控并行策略 (Priority: P3)

**Purpose**: 为开发者提供并行策略控制：最大并发数、强制串行、`--no-parallel`

**Goal**: 开发者可以灵活调整并行行为，不被强制并行

**Independent Test**: 在 tasks.md 中添加 `force_sequential` 注解或传入 `--no-parallel`，验证行为降级为串行

- [X] T005 [G2] [US3] Add strategy controls to `.claude/commands/speckit.implement.md`: support `max_concurrency` in tasks.md Parallel Groups table (default: no limit), support `force_sequential` annotation on individual tasks (remove from parallel group), support `--no-parallel` prompt instruction to force full serial execution, document backward compatibility: tasks.md without [G{n}] markers → original serial behavior

**Checkpoint**: 策略控制可用。所有 3 个 User Story 完成。

---

## Phase 4: Polish & 验证

**Purpose**: 端到端验证，确保向后兼容

- [X] T006 [G3] End-to-end validation: walk through a complete SDD cycle (specify → tasks → implement) with an existing spec to verify: 1) tasks.md output includes [G{n}] markers and Parallel Groups table, 2) implement correctly dispatches parallel sub-agents, 3) `--no-parallel` falls back to serial, 4) specs without [G{n}] markers behave identically to pre-modification

---

## Parallel Groups

| Group | Tasks | Depends On | Notes |
|-------|-------|------------|-------|
| G0    | T001, T002 | — | Setup, 串行 |
| G1    | T003, T004 | G0 | **并行执行** — T003 改 tasks 命令, T004 改 implement 命令，不同文件 |
| G2    | T005 | G1 | 串行 — 修改 implement 命令，依赖 G1 完成 |
| G3    | T006 | G2 | 串行 — 验证 |

**Max parallelism**: 2 (G1)
**Total groups**: 4
**Total tasks**: 6

---

## Implementation Strategy

### MVP (Phase 1 + Phase 2 only)

1. Complete T001, T002 → 理解现有结构
2. 并行执行 T003, T004 → 核心并行能力就位
3. **STOP and VALIDATE** — 用现有 spec 测试并行工作流

### Full Delivery

1. MVP 完成
2. Add T005 (策略控制)
3. Add T006 (端到端验证)
4. Complete

### 并行执行示例

```
# G1 并行分发（implement 命令的核心逻辑示意）:

Agent(
  description="US1: tasks命令并行组",
  prompt="修改 .claude/commands/speckit.tasks.md，添加 [G{n}] 并行组标记和依赖图...",
  isolation="worktree"
)  # T003

Agent(
  description="US2: implement命令编排器",
  prompt="修改 .claude/commands/speckit.implement.md，改为编排器模式...",
  isolation="worktree"
)  # T004
```
