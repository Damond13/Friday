# Implementation Plan: 交互模式加载指示器

**Branch**: `012-cli-ux-polish` | **Date**: 2026-06-07 | **Spec**: [spec.md](./spec.md)

## Summary

在 REPL 交互模式中，用户发送消息后、AI 回复到达前，使用 Rich 的 `Console.status()` 显示旋转加载动画。改动集中在 `display.py`（新增加载指示函数）和 `repl.py`（在 `_agent_reply` 中集成加载状态）。

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: Rich（已有依赖，提供 `Console.status()` 旋转动画能力）

**Storage**: N/A（纯 UI 特性，无数据存储）

**Testing**: pytest（CLI 层不写测试，参见 CLAUDE.md）

**Target Platform**: macOS Terminal / iTerm2 / VS Code 终端

**Project Type**: CLI 工具

**Performance Goals**: 动画不阻塞主线程，不影响 LLM 调用延迟

**Constraints**: 不引入新依赖；动画须在 Ctrl+C 时正确清理

**Scale/Scope**: 单用户 CLI，无并发需求

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原则 | 状态 | 说明 |
|------|------|------|
| I. 个人化优先 | ✅ 通过 | 加载指示提升个人交互体验 |
| II. 渐进式学习 | N/A | 不涉及学习功能 |
| III. 本地优先 | ✅ 通过 | 纯本地终端渲染，无外部依赖 |
| IV. 安全可控 | ✅ 通过 | 不涉及执行器或安全策略 |
| V. 简洁实用 | ✅ 通过 | 使用 Rich 内置能力，无额外花哨 UI |
| 模块边界 - cli/ | ✅ 通过 | 改动仅在 cli/ 模块内（display.py + repl.py） |
| 编码规范 - 200行/30行 | ✅ 通过 | 改动量极小，不影响文件大小 |
| 编码规范 - adapter 层 | ✅ 通过 | 不涉及外部调用 |
| 编码规范 - CLI 不写测试 | ✅ 通过 | 改动在 CLI 层，符合"不写测试"规范 |

**Gate Result**: PASS — 所有原则合规，无违规。

## Project Structure

### Documentation (this feature)

```text
specs/012-cli-ux-polish/
├── spec.md              # 功能规格
├── plan.md              # 本文件
└── tasks.md             # 任务列表（/speckit.tasks 生成）
```

### Source Code (repository root)

```text
src/friday/cli/
├── display.py           # 新增 show_loading() / hide_loading() 函数
└── repl.py              # 修改 _agent_reply() 集成加载指示

（其他模块不改动）
```

**Structure Decision**: 仅修改 `src/friday/cli/` 下两个文件，无新建文件。

## 设计方案

### 动画实现原理

Rich `Console.status()` 的动画机制：

1. **旋转字符序列** — 使用 Unicode Braille 字符循环替换（如 `⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏`），每隔约 80ms 切换到下一帧，形成旋转视觉效果
2. **终端光标控制** — 通过 ANSI 转义序列（`\r` 回车 + 覆写）在同一行反复刷新内容，每帧：回到行首 → 清除当前行 → 打印新字符
3. **与 print 共存** — status 活跃期间有其他 `console.print()` 时（如工具调用输出），Rich 暂时冻结动画行，将新输出打印在下方，然后在新位置恢复动画
4. **自动清理** — 退出 `with` 块时用 ANSI 序列清除动画行；即使 Ctrl+C 中断，`__exit__` 也会被调用清理

### 核心思路

Rich 的 `Console.status()` 提供了终端旋转动画能力，作为上下文管理器使用：

```
────────────────────────       ← Rule 分隔线
⠋ Friday 正在思考...           ← 加载动画（旋转中）
  🔧 shell_execute command=..  ← 工具调用输出（动画自动让位）
  ✓ 输出结果...                ← 工具结果
⠋ Friday 正在思考...           ← 动画继续
Friday: [回复内容]             ← 动画停止，显示回复
```

### 交互流程变更

**当前流程** (`_agent_reply`):

```
show_assistant_separator()  →  run_agent_loop()  →  console.print(reply)
（打印 "Friday: " 无换行）     （阻塞等待）         （回复接在 Friday: 后）
```

**新流程**:

```
show_assistant_separator()  →  [status spinner]  →  run_agent_loop()  →  [stop]  →  console.print(reply)
（只打印 Rule 分隔线）          （显示旋转动画）     （阻塞等待）         （停止动画） （打印 Friday: + 回复）
```

关键变更：`show_assistant_separator()` 不再打印 "Friday: " 前缀，改为在动画停止后、打印回复前显示。

### 改动清单

#### 1. `src/friday/cli/display.py`

- 修改 `show_assistant_separator()`：只打印 Rule 分隔线，不打印 "Friday: " 前缀
- 新增 `show_assistant_reply(reply: str)` 函数：打印 "Friday: " + 回复内容，与当前最终效果一致

#### 2. `src/friday/cli/repl.py`

- 修改 `_agent_reply()`：
  - 在 `run_agent_loop()` 调用外包裹 `console.status()` 上下文管理器
  - 用 `show_assistant_reply()` 替代直接 `console.print(result.reply)`

### 不改动的部分

- `src/friday/llm/agent.py` — Agent 循环逻辑不变
- `src/friday/cli/slash.py` — 斜杠命令处理不变
- `src/friday/cli/session.py` — 会话管理不变
- 其他所有模块

### 边界情况处理

- **Ctrl+C 中断**: `console.status()` 作为上下文管理器，`finally` 块中自动清理动画
- **LLM 错误**: `_agent_reply` 的 `except LLMError` 逻辑不变，`status` 上下文已在 `try` 外正确退出
- **快速响应 (<0.5s)**: Rich status 动画天然平滑，不会闪烁（至少显示一帧）

## Complexity Tracking

无需记录。无 Constitution 违规。
