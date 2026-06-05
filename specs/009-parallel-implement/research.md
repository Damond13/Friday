# Research: SDD 并行实现

**Date**: 2026-06-04 | **Feature**: 009-parallel-implement

## 调研 1: Claude Code Agent 并行调度模式

**Decision**: 使用 Claude Code Agent tool 的原生并发能力，在同一条消息中发出多个 Agent 调用实现并行

**Rationale**:
- Claude Code 支持在同一条响应中发出多个 Agent tool 调用，这些调用自动并发执行
- Agent tool 的 `isolation: "worktree"` 参数自动创建 git worktree，完成后自动合并或清理
- 主 Agent 通过 `run_in_background` 参数可以让子 Agent 在后台运行，完成后收到通知
- 主 Agent 也可以不设 `run_in_background`，直接在一条消息中发出多个 Agent 调用，等待全部结果返回

**Alternatives considered**:
1. **自行管理 worktree** — 通过 Bash 创建/合并 worktree：过于复杂，且 SDD 命令是 markdown 文件，不适合写复杂的 bash 逻辑
2. **使用子进程** — 不适用，Claude Code 没有子进程概念
3. **TaskCreate + 后台任务** — Claude Code 的 TaskCreate 是任务跟踪，不是并发执行机制

## 调研 2: 并行组标记在 tasks.md 中的格式

**Decision**: 扩展现有 `[P]` 标记为 `[G{n}]`（Group n）标记，在 tasks.md 末尾增加依赖关系汇总节

**Rationale**:
- 现有格式 `- [ ] T001 [P] [US1] Description` 已有 `[P]` 标记，`[G{n}]` 是自然扩展
- `[G0]` = 必须先完成的串行基础任务（无并行）
- `[G1]`, `[G2]`, ... = 可并行执行的组
- 末尾的依赖关系汇总让 implement 命令快速解析调度顺序
- 无 `[G{n}]` 标记的任务视为 Group 0（串行），保证向后兼容

**Alternatives considered**:
1. **纯 `[P]` + depends_on 字段** — `[P]` 只表示"可并行"，无法表达"这几个是一组"
2. **JSON/YAML 前置数据** — 在 tasks.md 前面放结构化数据，但破坏了 markdown 的可读性
3. **独立 scheduling.md 文件** — 增加额外文件，增加了工作流复杂度

## 调研 3: 子 Agent 上下文策略

**Decision**: 子 Agent 携带任务描述 + 相关文件路径 + plan.md 中对应 section 的摘要（精简上下文）

**Rationale**:
- 完整的 spec + plan + contracts 太大，会消耗大量上下文窗口
- 子 Agent 只需要知道"做什么"和"遵循什么规范"
- 精简上下文包含：任务描述、目标文件路径、相关的 coding standards 摘要、相关 entity/contract 定义
- 主 Agent 在分发时负责从 plan/spec 中提取精简上下文

**Alternatives considered**:
1. **完整上下文** — 每个子 Agent 都传完整 spec+plan：上下文窗口浪费大，可能超限
2. **最小上下文** — 只传任务描述：子 Agent 可能缺少必要的编码规范和接口定义，产出质量差
