# Implementation Plan: Agent 工具调用循环

**Branch**: `008-agent-tool-loop` | **Date**: 2026-06-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/008-agent-tool-loop/spec.md`

## Summary

实现 LLM 工具调用闭环：将已有的工具定义（tools.py）传给 LLM，检测 tool_call 响应，路由到对应执行器，将结果回传 LLM，循环直到得到最终文本回复。同时实现安全确认机制和可视化反馈。

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: OpenAI SDK（已集成）、asyncio、Typer + Rich（CLI 层）

**Storage**: N/A（运行时状态，不持久化）

**Testing**: pytest + pytest-asyncio

**Target Platform**: macOS / Linux 本地 CLI

**Project Type**: CLI 工具

**Performance Goals**: 工具调用 5 秒内开始执行

**Constraints**: 流式输出和工具调用互斥，tool_call 轮次用非流式，最终回复用流式

**Scale/Scope**: 单用户本地使用，最多 10 轮工具调用循环

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原则 | 检查结果 |
|------|---------|
| I. 个人化优先 | ✅ 工具调用让 Friday 能真正帮用户做事 |
| II. 渐进式学习 | ✅ 不涉及 |
| III. 本地优先 | ✅ 所有执行在本地完成 |
| IV. 安全可控 | ✅ 安全确认机制覆盖 shell 危险命令和文件覆写 |
| V. 简洁实用 | ✅ 工具过程简洁展示 |
| 编码规范 | ✅ 文件 <200 行，函数 <30 行，类型注解 |
| 模块边界 | ✅ agent 循环在 llm/ 层，执行逻辑复用 executor/ |
| 测试规范 | ✅ 只在 implement 阶段运行相关测试 |

**Gate**: PASS

## Project Structure

### Documentation (this feature)

```text
specs/008-agent-tool-loop/
├── plan.md
├── data-model.md
├── contracts/
│   └── tool-executors.md
└── tasks.md              # Phase 2 output
```

### Source Code (changes)

```text
src/friday/
├── llm/
│   ├── agent.py          # 新增：Agent 循环控制器
│   ├── executors.py      # 新增：工具执行器注册与实现
│   ├── adapter.py        # 修改：无变化（已支持 tools 参数）
│   ├── tools.py          # 修改：无变化（工具定义已就绪）
│   ├── types.py          # 修改：新增 ToolResult 数据类
│   └── prompts.py        # 修改：已增强（上一个 commit）
├── cli/
│   └── repl.py           # 修改：_stream_reply 改用 agent loop
├── executor/
│   └── (不变)            # 复用已有 execute() + set_confirm_callback()
└── knowledge/
    └── (不变)            # 复用已有 adapter.search()

tests/
└── unit/
    └── test_agent.py     # 新增：Agent 循环单元测试
```

**Structure Decision**: 在现有 `llm/` 模块内新增 2 个文件（agent.py、executors.py），修改 3 个文件（types.py、repl.py、prompts.py）。不改已有模块的核心逻辑。

## 实现步骤

### Step 1: 新增 ToolResult 类型 (`llm/types.py`)

在现有 `ToolCall` 类后面新增 `ToolResult` 数据类：

```python
@dataclass
class ToolResult:
    tool_call_id: str
    success: bool
    output: str
```

### Step 2: 新增工具执行器 (`llm/executors.py`)

工具名 → 执行函数的注册表，每个执行器接收 `dict` 参数，返回 `ToolResult`。

四个执行器：
- **shell_execute**: 调用 `executor.execute()`（已有的安全分级+确认+历史）
- **file_read**: 同步读文件，支持 offset/limit
- **file_write**: 写文件前检查目标是否存在，存在则需确认
- **knowledge_search**: 调用 `knowledge.adapter.search()`

注册表结构：
```python
_EXECUTORS: dict[str, Callable[[dict], Awaitable[ToolResult]]] = {}
```

提供 `get_executor(name)` 和 `register_executor(name, fn)` 公共 API。

### Step 3: 新增 Agent 循环控制器 (`llm/agent.py`)

核心函数 `run_agent_loop(messages, context)`：

```
1. 注入 system prompt（复用 _inject_system_prompt）
2. 传入工具定义（get_tool_definitions()）
3. 调用 chat()（非流式，检测 tool_call）
4. 如果 response.tool_calls 非空：
   a. 记录 assistant 消息（含 tool_calls）
   b. 逐个执行工具调用
   c. 将 ToolResult 转为 tool 消息追加到 messages
   d. round_count++，回到步骤 3
5. 如果 response.tool_calls 为空：
   a. 返回最终文本回复
   b. 包含完整 messages（用于 session 保存）
```

返回值设计：
```python
@dataclass
class AgentResult:
    reply: str                    # 最终文本回复
    messages: list[dict]          # 完整消息历史（含 tool 交互）
    tool_calls_count: int         # 工具调用总次数
```

关键细节：
- 每轮工具执行前，通过回调通知 CLI 层展示（工具名、参数）
- 每轮工具执行后，通过回调通知 CLI 展示结果摘要
- 超限时返回提示信息而非抛异常
- 工具执行异常时，将错误信息作为 ToolResult 回传 LLM

### Step 4: 修改 REPL (`cli/repl.py`)

将 `_stream_reply()` 改为调用 `run_agent_loop()`：

```
1. 调用 run_agent_loop(session.messages, context)
2. 展示过程中的工具调用反馈（通过回调）
3. 最终回复用流式展示（run_agent_loop 返回的 reply 直接打印）
4. 保存完整 messages 到 session
```

注册确认回调：在 `run_repl()` 启动时调用 `set_confirm_callback()` 注册 CLI 层的确认函数。

### Step 5: 可视化反馈 (`cli/display.py`)

新增两个展示函数：
- `show_tool_call(name, arguments)` — 显示正在调用的工具和参数
- `show_tool_result(success, output)` — 显示工具执行结果摘要

### Step 6: 单元测试 (`tests/unit/test_agent.py`)

测试用例：
- 普通对话不触发工具调用
- LLM 返回单个 tool_call 时正确路由执行
- LLM 返回多个 tool_call 时依次执行
- 工具执行错误时错误信息回传 LLM
- 超过最大轮次时停止并提示
- file_write 覆写已有文件时触发确认
