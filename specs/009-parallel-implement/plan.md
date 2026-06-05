# Implementation Plan: SDD 并行实现

**Branch**: `009-parallel-implement` | **Date**: 2026-06-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/009-parallel-implement/spec.md`

## Summary

改造 SDD 工作流的 tasks 和 implement 两个命令，使其支持并行任务执行。tasks 命令增加并行组（group）识别和依赖图生成；implement 命令从单 Agent 串行模式改为编排器模式，通过 Claude Code 的 `Agent(..., isolation="worktree")` 并发调度子 Agent。改造范围仅限 `.claude/commands/` 下的 markdown 指令文件，不涉及 Python 代码。

## Technical Context

**Language/Version**: Markdown（Claude Code 命令指令文件）

**Primary Dependencies**: Claude Code Agent tool（原生 `isolation: "worktree"` 支持）

**Storage**: N/A

**Testing**: 手动验证 — 构造示例 tasks.md 运行完整工作流

**Target Platform**: Claude Code CLI

**Project Type**: SDD 工作流命令改造

**Performance Goals**: 3+ 可并行任务时，执行时间比串行减少 ≥30%

**Constraints**: 改造仅限 `.claude/commands/` 目录下 2 个 markdown 文件；向后兼容（无并行组时行为不变）

**Scale/Scope**: 2 个命令文件修改，影响后续所有 SDD 工作流执行

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原则 | 状态 | 评估 |
|------|------|------|
| I. 个人化优先 | PASS | 并行实现提升开发效率，间接提升个人化体验 |
| II. 渐进式学习 | PASS | 并行是开发流程优化，不影响学习机制 |
| III. 本地优先 | PASS | 所有操作在本地 git worktree 中完成 |
| IV. 安全可控 | PASS | 子 Agent 失败时暂停报告（FR-008），用户始终有最终决定权 |
| V. 简洁实用 | PASS | 默认行为不变，并行只在有并行组时触发 |
| 编码规范 | N/A | 本次不涉及 Python 代码 |
| 测试执行规范 | PASS | 改造的是 markdown 命令，不触发 pytest |
| 模块边界 | PASS | 不影响任何 Python 模块 |

**Result**: PASS — 无违反，无需 Complexity Tracking。

## Project Structure

### Documentation (this feature)

```text
specs/009-parallel-implement/
├── spec.md              # 功能规格
├── plan.md              # 本文件
├── research.md          # 调研：Claude Code 并行调度模式
├── contracts/
│   └── task-format.md   # tasks.md 并行组格式契约
└── tasks.md             # 任务分解（/speckit.tasks 产出）
```

### Source Code (repository root)

```text
.claude/commands/
├── speckit.tasks.md       # [改造] 增加并行组识别和依赖图
└── speckit.implement.md   # [改造] 编排器模式 + 并行 Agent 调度
```

**Structure Decision**: 仅修改 2 个现有 markdown 命令文件，不新增文件。

## Complexity Tracking

无 Constitution 违反，不需要记录。
