# Tasks: 执行器模块

**Input**: Design documents from `/specs/004-executor/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/executor-api.md

**Tests**: 本项目 CLAUDE.md 要求"测试覆盖核心逻辑"，但 spec 未显式要求 TDD。测试任务标记为可选，在 Polish 阶段执行。

**Organization**: 按用户故事组织任务，每个故事可独立实现和测试。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行执行（不同文件，无依赖）
- **[Story]**: 所属用户故事（US1, US2, US3, US4）
- 描述包含精确文件路径

---

## Phase 1: Setup（项目初始化）

**Purpose**: 创建模块文件结构和基础常量

- [x] T001 创建执行器模块文件结构：src/friday/executor/ 下创建 __init__.py, runner.py, safety.py, output.py, history.py, adapter.py 的空文件
- [x] T002 [P] 创建测试目录结构：tests/unit/ 下创建 test_runner.py, test_safety.py, test_output.py, test_history.py 的空文件，tests/conftest.py 创建 pytest fixture

---

## Phase 2: Foundational（阻塞性前置条件）

**Purpose**: 所有用户故事依赖的核心基础设施，MUST 完成后才能开始任何用户故事

**⚠️ CRITICAL**: 安全策略和类型定义是所有故事的前置依赖

- [x] T003 实现 SafetyLevel 枚举和命令安全分类函数 classify() 在 src/friday/executor/safety.py，包含白名单（ls, pwd, cat, head, tail, echo, wc, find, grep, which, date, whoami, uname, git, diff, tree, file, stat）和黑名单正则（rm -rf, sudo, chmod, mkfs, dd, shutdown, reboot 等）
- [x] T004 [P] 定义 ExecutionResult 和 StreamChunk 数据类在 src/friday/executor/runner.py，包含 command, exit_code, stdout, stderr, duration_ms, safety_level, approved, truncated 字段
- [x] T005 [P] 定义 ExecutorError 异常层级在 src/friday/executor/adapter.py：ExecutorError 基类、CommandTimeoutError、CommandDeniedError、CommandNotFoundError

**Checkpoint**: 基础设施就绪 — 安全分类可用，类型和异常定义完成

---

## Phase 3: User Story 1 - 基础命令执行 (Priority: P1) 🎯 MVP

**Goal**: 用户可以执行安全命令并获得结果输出

**Independent Test**: 调用 execute("echo hello") 返回正确结果，safety_level 为 safe

- [x] T006 [US1] 实现异步命令执行引擎 run() 在 src/friday/executor/runner.py，使用 asyncio.create_subprocess_shell 执行命令，捕获 stdout/stderr，计算耗时，返回 ExecutionResult
- [x] T007 [P] [US1] 实现输出处理函数 format_output() 和 summarize_output() 在 src/friday/executor/output.py，短输出（≤20行）原样返回，长输出截断标记
- [x] T008 [US1] 实现统一执行接口 execute() 在 src/friday/executor/adapter.py，串联 safety.classify() → runner.run() → output.format_output()，返回最终 ExecutionResult

**Checkpoint**: execute("ls -la") 可正常执行并返回结果，安全命令自动执行

---

## Phase 4: User Story 2 - 分级安全确认 (Priority: P2)

**Goal**: 新指令和危险命令需要用户确认，用户可信任命令跳过确认

**Independent Test**: execute("rm test.txt") 触发确认回调，确认后执行；trust_command 后相同命令自动执行

- [x] T009 [US2] 实现 confirm 回调机制和 set_confirm_callback() 在 src/friday/executor/adapter.py，包含 ConfirmCallback 类型定义和全局回调存储
- [x] T010 [US2] 实现信任命令管理 add_trusted() 和 is_trusted() 在 src/friday/executor/safety.py，使用 SQLite trusted_commands 表存储用户信任
- [x] T011 [US2] 在 adapter.py 的 execute() 中集成确认流程：dangerous 每次确认、confirm 首次确认后自动信任、safe 直接执行，被拒绝时抛出 CommandDeniedError

**Checkpoint**: 三级安全策略完整工作，dangerous 每次确认，confirm 首次确认后记住

---

## Phase 5: User Story 3 - 命令超时与异常处理 (Priority: P3)

**Goal**: 超时命令自动终止，命令不存在等异常有友好提示

**Independent Test**: execute("sleep 60", timeout=1) 抛出 CommandTimeoutError；execute("nonexistent_cmd") 返回友好错误

- [x] T012 [US3] 在 runner.py 的 run() 中集成 asyncio.wait_for 超时控制，超时时先 terminate() 再 kill()，抛出 CommandTimeoutError
- [x] T013 [US3] 在 runner.py 中实现 SIGINT 信号转发，Ctrl+C 时优雅终止子进程并恢复交互状态
- [x] T014 [US3] 在 output.py 中实现 format_error() 友好错误格式化，覆盖：命令不存在（exit code 127）、权限不足（126）、超时、被拒绝

**Checkpoint**: 超时和异常场景全部有友好处理

---

## Phase 6: User Story 4 - 命令历史与日志 (Priority: P4)

**Goal**: 每次执行自动记录历史，用户可查询最近执行记录

**Independent Test**: 执行若干命令后 get_history(10) 返回完整记录列表

- [x] T015 [US4] 创建 SQLite schema（execution_log 和 trusted_commands 表）和初始化函数 init_db() 在 src/friday/executor/history.py，DB 路径 ~/.friday/executor.db，WAL 模式
- [x] T016 [US4] 实现执行记录存储 save_record() 和查询 get_history() 在 src/friday/executor/history.py，stdout/stderr 截断至 4KB，按 started_at 降序查询
- [x] T017 [US4] 在 adapter.py 的 execute() 中集成历史记录，执行完成后自动调用 history.save_record()

**Checkpoint**: 执行历史完整记录，get_history 可查询

---

## Phase 7: Polish & Cross-Cutting

**Purpose**: 流式输出、公共 API 导出、端到端验证

- [x] T018 [P] 实现流式执行接口 execute_stream() 在 src/friday/executor/adapter.py，yield StreamChunk，逐步产出 stdout/stderr
- [x] T019 在 src/friday/executor/__init__.py 中导出公共 API：execute, execute_stream, get_history, trust_command, set_confirm_callback, ExecutionResult, StreamChunk, SafetyLevel, ExecutorError
- [x] T020 实现 history.py 的历史清理 clean_old_records()，删除 90 天前的记录，在 init_db() 时自动执行
- [x] T021 端到端验证：按 quickstart.md 的 5 个测试场景手动验证所有功能

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 无依赖，立即开始
- **Foundational (Phase 2)**: 依赖 Setup 完成 — 阻塞所有用户故事
- **US1 (Phase 3)**: 依赖 Foundational — MVP 核心
- **US2 (Phase 4)**: 依赖 US1（在 adapter.py 基础上增加确认流程）
- **US3 (Phase 5)**: 依赖 US1（在 runner.py 基础上增加超时和信号处理）
- **US4 (Phase 6)**: 依赖 US1（在 adapter.py 基础上集成历史记录）
- **Polish (Phase 7)**: 依赖 US1-US4 全部完成

### User Story Dependencies

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational)
    ↓
Phase 3 (US1 - 基础执行) 🎯 MVP
    ↓
    ├── Phase 4 (US2 - 安全确认)
    ├── Phase 5 (US3 - 超时异常)
    └── Phase 6 (US4 - 历史日志)
         ↓
    Phase 7 (Polish)
```

### Parallel Opportunities

- Phase 1: T001 和 T002 可并行
- Phase 2: T003, T004, T005 可并行（不同文件）
- Phase 3: T006 和 T007 可并行（runner.py 和 output.py 无依赖）
- Phase 4-6: US2、US3、US4 修改不同文件时可并行（safety.py / runner.py / history.py）
- Phase 7: T018 和 T020 可并行

---

## Parallel Example: Phase 2

```bash
# 三个任务并行执行（不同文件）：
Task T003: "实现 SafetyLevel 和 classify() 在 safety.py"
Task T004: "定义 ExecutionResult/StreamChunk 在 runner.py"
Task T005: "定义异常层级在 adapter.py"
```

## Parallel Example: Phase 3

```bash
# 两个任务并行执行：
Task T006: "实现 run() 在 runner.py"
Task T007: "实现 format_output/summarize 在 output.py"
# 然后：
Task T008: "实现 execute() 在 adapter.py"（依赖 T006, T007）
```

---

## Implementation Strategy

### MVP First（仅 User Story 1）

1. 完成 Phase 1: Setup
2. 完成 Phase 2: Foundational
3. 完成 Phase 3: US1 基础命令执行
4. **验证**: execute("echo hello") 正常返回
5. 此时 Friday 已具备最基本的命令执行能力

### Incremental Delivery

1. Setup + Foundational → 基础就绪
2. US1 基础执行 → **MVP 可用！**
3. US2 安全确认 → 安全保障完善
4. US3 超时异常 → 生产可靠性
5. US4 历史日志 → 可追溯性
6. Polish → 流式输出 + API 导出 + 清理

---

## Notes

- [P] 任务 = 不同文件，无依赖冲突
- [Story] 标签将任务映射到具体用户故事
- 每个用户故事独立可测试
- US2/US3/US4 在 US1 基础上增量开发，修改不同文件
- adapter.py 是贯穿始终的集成点，每个阶段都在其上增加功能
