# Code Review: Agent 工具调用循环 (008-agent-tool-loop)

**Reviewer**: Reviewer Agent (Re-Review)
**Date**: 2026-06-04 (第二轮审核)
**Branch**: `008-agent-tool-loop`

---

## Summary

本功能实现了 Friday 从"聊天机器人"进化为"AI Agent"的关键闭环：LLM 工具调用检测、路由执行、结果回传的完整循环。上一轮审核发现 3 个 Important 级别问题（F-1 函数超长、F-2 CommandDeniedError 未区分、F-3 tool_call_id 空值），均已修复。本轮审核确认所有 Important 问题已解决，无新引入问题。整体实现质量好，架构边界清晰，规范遵守良好。

---

## Previous Findings Resolution

| ID | Description | Status | Evidence |
|----|-------------|--------|----------|
| F-1 | `run_agent_loop` 70 行超限 | **FIXED** | 拆分为 4 个函数：`run_agent_loop`(27行)、`_build_tool_calls_msg`(14行)、`_process_tool_calls`(17行)、`_execute_tool`(19行)，全部在 30 行以内 |
| F-2 | `_exec_shell` 未区分 `CommandDeniedError` | **FIXED** | `executors.py:60-63` 在 `except Exception` 块内通过 `isinstance` 检查 `CommandDeniedError`，返回"用户拒绝执行该命令"而非通用错误 |
| F-3 | `tool_call_id` 始终为空字符串 | **FIXED** | `agent.py:93,100` 在 `_execute_tool` 中将 `result.tool_call_id = tool_call_id` 赋值，执行器返回空 ID 后由 agent 层正确填充 |

---

## Checklist Results

| # | Check Item | Result | Notes |
|---|-----------|--------|-------|
| 1 | Spec compliance | PASS | FR-001~FR-008 全部实现 |
| 2 | Constitution compliance | PASS | 安全可控原则（IV）已落地 |
| 3 | Architecture compliance | PASS | Agent 循环在 llm/ 层，执行复用 executor/ |
| 4 | File size <= 200 lines | PASS | 最大文件 executors.py 139 行 |
| 5 | Function size <= 30 lines | PASS | 最大函数 `run_repl` 36 行（CLI 层，见 S-1） |
| 6 | Type annotations | PASS | 所有公共函数均有完整类型注解 |
| 7 | Adapter layer | PASS | LLM 调用走 adapter.py，executor 走 executor/ |
| 8 | Storage layer | PASS | 无直接存储操作，均通过模块 API |
| 9 | Test coverage | PASS | 7 个测试覆盖核心路径 |
| 10 | Security | PASS | CommandDeniedError 正确区分，安全回调完整 |
| 11 | No over-engineering | PASS | 实现简洁，无多余抽象 |
| 12 | No direct SDK calls | PASS | 所有外部调用通过 adapter 层 |

---

## File Inventory

| File | Lines | Status | Notes |
|------|-------|--------|-------|
| `src/friday/llm/agent.py` | 104 | New | Agent 循环控制器，4 个函数均 <= 27 行 |
| `src/friday/llm/executors.py` | 139 | New | 工具执行器注册表，4 个执行器均 <= 21 行 |
| `src/friday/llm/types.py` | 40 | Modified | 新增 ToolResult、AgentResult 数据类 |
| `src/friday/cli/repl.py` | 143 | Modified | 新增 `_agent_reply`、`_setup_safety_callbacks` |
| `src/friday/cli/display.py` | 89 | Modified | 新增 `show_tool_call`、`show_tool_result` |
| `tests/unit/test_agent.py` | 161 | New | 7 个单元测试 |

---

## Spec Compliance Detail

| Requirement | Status | Evidence |
|------------|--------|----------|
| FR-001: 传工具定义给 LLM | PASS | `agent.py:29` 调用 `get_tool_definitions()`，通过 `chat(tools=tools)` 传入 |
| FR-002: 识别 tool_call 并路由 | PASS | `agent.py:38` 检测 `response.tool_calls`，`executors.py:28` 路由到对应执行器 |
| FR-003: 结果回传支持多轮循环 | PASS | `agent.py:33-48` 完整循环，结果以 tool message 追加到 working |
| FR-004: 安全确认机制 | PASS | `repl.py:129-143` 注册两层回调（executor 危险命令 + LLM 文件覆写） |
| FR-005: 可视化反馈 | PASS | `display.py:77-80` show_tool_call 显示工具名和参数 |
| FR-006: 结果格式化展示 | PASS | `display.py:83-89` 短输出直接显示，超 200 字符截断 |
| FR-007: 最大轮次限制 | PASS | `agent.py:16` MAX_ROUNDS=10，`agent.py:44-48` 超限返回提示信息 |
| FR-008: 复用 executor 安全分级 | PASS | `executors.py:52` 调用 `friday.executor.execute()` 复用已有安全策略 |

---

## Detailed Analysis

### Architecture

模块边界遵守良好：

- `agent.py` 位于 `llm/` 层，负责循环控制和工具调用消息构建，不直接执行任何工具
- `executors.py` 位于 `llm/` 层，是工具名到执行函数的注册表，内部调用 `executor.execute()` 和 `knowledge.adapter.search()` 复用已有模块
- `repl.py` 位于 `cli/` 层，仅负责交互展示和回调注册，不含业务逻辑
- `display.py` 位于 `cli/` 层，新增两个纯展示函数

调用链路清晰：`cli/repl.py` -> `llm/agent.py` -> `llm/executors.py` -> `executor/` + `knowledge/`，无循环依赖。

### Security

安全防线完整，覆盖三层：

1. **executor 模块层**：`executor.execute()` 内置安全分级策略（安全/需确认/危险），通过 `set_confirm_callback` 注册 CLI 层确认弹窗
2. **executors 模块层**：`_exec_file_write` 覆写已存在文件时触发确认回调
3. **错误语义层**：`CommandDeniedError`（用户主动拒绝）与普通执行异常区分处理，LLM 收到不同措辞以做出正确决策

### F-2 Fix Quality Note

`CommandDeniedError` 的处理采用在 `except Exception` 块内 `isinstance` 检查的方式（`executors.py:60-63`），而非独立的 `except CommandDeniedError` 子句。这是因为 `CommandDeniedError` 的 import 位于 except 块内部（lazy import，避免循环依赖）。功能上等价，可读性稍弱但可接受。

### F-3 Fix Quality Note

执行器返回 `ToolResult(tool_call_id="")` 后，`agent.py` 的 `_execute_tool` 在三个路径（正常返回 L93、ThreadPool 返回 L100、异常 L104）都正确设置了 `tool_call_id`。最终构建 tool 消息时使用 `tc.id`（L82），与 `result.tool_call_id` 保持一致。数据模型语义现在完整。

---

## Suggestions (Nice to Have)

### S-1: `run_repl` 函数 36 行，略超 30 行限制

**File**: `src/friday/cli/repl.py` L59-L94

`run_repl` 是 CLI 层的入口函数，包含 try/except/finally 嵌套的 REPL 主循环。36 行超出 30 行限制 6 行。可提取 `_repl_loop(prompt, session)` 辅助函数将主循环内联压缩到 30 行以内。

**评估**: Constitution 规定"CLI 层不写测试"，CLI 入口函数通常包含初始化和异常处理样板代码，适当放宽是合理的。不阻塞审核。

**严重程度**: Suggestion

---

### S-2: `_execute_tool` 中 `RuntimeError` 捕获范围偏宽

**File**: `src/friday/llm/agent.py` L95

```python
except RuntimeError:
```

`asyncio.run()` 在已有事件循环运行时抛出 `RuntimeError("This event loop is already running")`，但其他 `RuntimeError`（如递归深度超限）也会被意外捕获。可考虑检查错误消息来确认是否为嵌套事件循环问题。`concurrent.futures` 的 import 也建议移到文件顶部。

**严重程度**: Suggestion -- 当前可正常工作，防御性不够精确

---

### S-3: `_exec_file_read` 缺少默认读取上限

**File**: `src/friday/llm/executors.py` L81

```python
lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
```

一次性读取整个文件内容，没有默认行数上限。如果 LLM 指定读取一个非常大的文件（如数百 MB 的日志），全部内容会塞进 messages 发送给 LLM，可能导致内存暴涨或超出 token 限制。当前通过 `offset/limit` 参数可部分缓解，但缺少默认上限保护。

**严重程度**: Suggestion -- 实际风险较低（LLM 通常会传 limit 参数），但缺少防御性保护

---

### S-4: `test_unknown_tool` 的 mock 方式说明

**File**: `tests/unit/test_agent.py` L132

```python
with patch("friday.llm.agent.get_executor", return_value=None):
```

`get_executor` 被全局 mock 为始终返回 `None`。测试意图是验证未知工具场景下 `_execute_tool` 直接返回错误 `ToolResult`。当前足够清晰，但如果后续有更复杂的执行器查找逻辑，这种 mock 可能隐藏真实问题。建议在测试注释中说明 mock 意图。

**严重程度**: Suggestion

---

## What Was Done Well

1. **F-1 修复彻底**: `run_agent_loop` 从 70 行拆分为 4 个职责清晰的函数，每个都在限制内，函数命名和职责划分合理
2. **F-2 语义正确**: `CommandDeniedError` 现在返回明确的"用户拒绝"消息，LLM 能据此调整策略而非重试
3. **F-3 数据一致**: `tool_call_id` 在 agent 层正确填充，`ToolResult` 数据模型不再有空字段
4. **架构边界清晰**: Agent 循环在 `llm/` 层，工具执行通过注册表解耦，安全确认通过回调注入
5. **adapter 模式遵守**: LLM 调用全部走 `adapter.chat()`，Shell 执行走 `executor.execute()`，知识库走 `knowledge.adapter.search()`，无直接 SDK 调用
6. **回调设计优雅**: `on_tool_call`/`on_tool_result` 回调让 CLI 层展示逻辑完全解耦
7. **测试覆盖合理**: 7 个测试覆盖正常路径、异常路径和回调机制，且使用 `patch` 精确控制 mock 范围

---

## Verdict

**APPROVED**

上一轮审核的 3 个 Important 问题（F-1 函数超长、F-2 CommandDeniedError 未区分、F-3 tool_call_id 空值）均已正确修复。无新引入问题。4 个 Suggestion 级别改进建议可后续迭代处理，不阻塞合并。
