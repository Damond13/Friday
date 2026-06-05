# Contract: tasks.md 并行组格式

**Date**: 2026-06-04 | **Feature**: 009-parallel-implement

## 概述

定义 `tasks.md` 中并行组的标记格式，作为 tasks 命令（生产方）和 implement 命令（消费方）之间的契约。

## 任务行格式

```
- [ ] {TaskID} [G{n}] [P] [US{x}] Description with file path
```

### 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `- [ ]` / `- [x]` | 是 | Markdown checkbox |
| `{TaskID}` | 是 | T001, T002, ... 顺序编号 |
| `[G{n}]` | 否 | Group 编号，n 从 0 开始。省略时默认 G0（串行基础任务） |
| `[P]` | 否 | 可并行标记（兼容旧格式，有 `[G{n}]` 时冗余但保留可读性） |
| `[US{x}]` | 条件必填 | 用户故事编号，仅在 User Story phase 必填 |
| Description | 是 | 任务描述 + 目标文件路径 |

### 示例

```markdown
## Phase 1: Setup
- [ ] T001 Create project structure per implementation plan

## Phase 2: Foundational
- [ ] T002 [G0] Create base types in src/types.py
- [ ] T003 [G0] Create config module in src/config.py

## Phase 3: User Story 1
- [ ] T004 [G1] [P] [US1] Create ToolResult dataclass in src/llm/types.py
- [ ] T005 [G1] [P] [US1] Create executor registry in src/llm/executors.py
- [ ] T006 [G1] [P] [US1] Create shell executor in src/llm/executors.py

## Phase 4: User Story 2
- [ ] T007 [G2] [US2] Create Agent loop in src/llm/agent.py
```

## 依赖关系汇总节

tasks.md 末尾必须包含以下节（由 tasks 命令自动生成）：

```markdown
## Parallel Groups

| Group | Tasks | Depends On | Notes |
|-------|-------|------------|-------|
| G0    | T002, T003 | — | Foundational, 串行 |
| G1    | T004, T005, T006 | G0 | 并行执行 |
| G2    | T007 | G1 | 串行 |

**Max parallelism**: 3 (G1)
**Total groups**: 3
```

### 字段说明

| 字段 | 说明 |
|------|------|
| Group | 并行组编号 |
| Tasks | 属于该组的任务 ID 列表 |
| Depends On | 前置依赖组（`—` 表示无依赖） |
| Notes | 执行策略备注 |

## 向后兼容

- 无 `[G{n}]` 标记的任务 → 视为 G0（串行）
- 无 `## Parallel Groups` 节 → implement 命令按原有串行模式执行
- 有 `[P]` 但无 `[G{n}]` → 视为可并行但未分组，implement 命令将所有 `[P]` 任务视为同组
