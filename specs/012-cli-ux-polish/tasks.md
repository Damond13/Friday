# Tasks: 交互模式加载指示器

**Input**: Design documents from `/specs/012-cli-ux-polish/`

**Prerequisites**: plan.md (required), spec.md (required)

**Tests**: CLI 层不写测试（CLAUDE.md 规定）。本功能为纯 UI 展示改动，低风险，无测试任务。

**Organization**: 按用户故事分组，支持独立实现和验证。

## Format: `[ID] [G{n}] [P?] [Story] Description`

- **[G{n}]**: 并行组号，同组可并行
- **[P]**: 可并行（不同文件，无依赖）
- **[Story]**: 所属用户故事（US1/US2/US3）

## Phase 1: User Story 1 - 等待响应时的视觉反馈 (Priority: P1) 🎯 MVP

**Goal**: 用户发送消息后，等待 AI 回复期间显示旋转加载动画

**Independent Test**: 在交互模式发送任意消息，观察消息发出后、回复出现前是否有旋转加载动画

### Implementation for User Story 1

- [x] T001 [G0] [US1] 修改 `show_assistant_separator()` 和新增 `show_assistant_reply()` in `src/friday/cli/display.py`：移除 "Friday: " 前缀打印逻辑，新增 `show_assistant_reply(reply: str)` 函数用于打印 "Friday: " + 回复内容
- [x] T002 [G1] [US1] 修改 `_agent_reply()` 集成 `console.status()` 加载动画 in `src/friday/cli/repl.py`：用 `console.status("Friday 正在思考...")` 包裹 `run_agent_loop()` 调用，用 `show_assistant_reply()` 替代直接 `console.print(result.reply)`

**Checkpoint**: 此时交互模式应显示加载动画，用户发送消息后能看到旋转指示器

---

## Phase 2: User Story 2 + 3 - 展示质量优化 (Priority: P2 + P3)

**Goal**: 加载动画不影响回复展示质量；快速响应时动画平滑不闪烁

**Independent Test**: 发送消息后检查回复内容展示是否完整无残留；发送简单消息（如"你好"）检查是否无闪烁

### Verification for User Story 2 & 3

- [x] T003 [G0] [US2] 验证 `display.py` 改动后的展示效果：确认 `show_assistant_reply()` 打印的回复内容从分隔线后正常开始，无多余空行或残留字符；如有问题则修复 `src/friday/cli/display.py`
- [x] T004 [G0] [US3] 验证快速响应场景：确认 Rich `console.status()` 在 LLM 极速返回时动画平滑过渡无闪烁；如有闪烁问题则添加最小显示时间机制到 `src/friday/cli/repl.py`

**Checkpoint**: 所有用户故事验证通过，功能完整

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (US1)**: 无前置依赖，可立即开始
- **Phase 2 (US2+US3)**: 依赖 Phase 1 完成

### Within Phase 1

- T001 先行（修改 display.py 导出函数）
- T002 依赖 T001（调用新的 `show_assistant_reply` 函数）

### Within Phase 2

- T003、T004 可并行（验证不同方面）

---

## Parallel Groups

| Group | Tasks  | Depends On | Notes              |
|-------|--------|------------|--------------------|
| G0    | T001   | —          | display.py 改动    |
| G1    | T002   | G0         | repl.py 改动       |
| G2    | T003, T004 | G1     | 验证任务，可并行   |

**Max parallelism**: 2
**Total groups**: 3

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. 完成 T001（display.py 改动）
2. 完成 T002（repl.py 改动）
3. 手动启动 Friday，发送消息验证加载动画效果

### Full Delivery

4. 验证 US2（展示质量）
5. 验证 US3（快速响应平滑度）
6. 如有问题修复，无问题则标记完成
