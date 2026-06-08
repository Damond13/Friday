# Implementation Plan: 知识库添加工具

**Branch**: `013-knowledge-add-tool` | **Date**: 2026-06-08 | **Spec**: [spec.md](./spec.md)

## Summary

为 LLM Agent 新增 `knowledge_add` 工具，让 AI 能通过工具调用直接向知识库添加笔记。改动集中在 `tools.py`（新增工具定义）和 `executors.py`（新增执行器），复用现有 `knowledge/adapter.py` 的 `add_note` 函数。

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: 无新依赖，复用现有 knowledge 模块

**Storage**: 复用现有知识库存储层（笔记文件 + FTS 索引 + ChromaDB 向量索引）

**Testing**: pytest

**Target Platform**: macOS Terminal / iTerm2 / VS Code 终端

**Project Type**: CLI 工具

**Performance Goals**: 笔记添加 < 1 秒

**Constraints**: 不引入新依赖；复用 `adapter.add_note` 不重复实现

**Scale/Scope**: 单用户 CLI

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原则 | 状态 | 说明 |
|------|------|------|
| I. 个人化优先 | ✅ 通过 | 让用户通过对话自然积累知识，核心个人化能力 |
| II. 渐进式学习 | N/A | 不涉及学习功能 |
| III. 本地优先 | ✅ 通过 | 数据存储在本地知识库 |
| IV. 安全可控 | ✅ 通过 | 知识添加为安全操作，无需确认 |
| V. 简洁实用 | ✅ 通过 | 复用现有模块，最小改动 |
| 模块边界 - llm/ | ✅ 通过 | tools.py 定义工具，executors.py 注册执行器 |
| 模块边界 - knowledge/ | ✅ 通过 | 复用 adapter.add_note，不修改 knowledge 模块 |
| 编码规范 - 200行/30行 | ✅ 通过 | 预计每个文件增加 < 30 行 |
| 编码规范 - adapter 层 | ✅ 通过 | executors.py 调用 knowledge.adapter，不直接操作存储 |

**Gate Result**: PASS — 所有原则合规，无违规。

## Project Structure

### Documentation (this feature)

```text
specs/013-knowledge-add-tool/
├── spec.md              # 功能规格
├── plan.md              # 本文件
└── tasks.md             # 任务列表（/speckit.tasks 生成）
```

### Source Code (repository root)

```text
src/friday/llm/
├── tools.py             # 新增 KNOWLEDGE_ADD 工具定义 + 注册到 get_tool_definitions()
└── executors.py         # 新增 _exec_knowledge_add 执行器 + 注册

（其他模块不改动）
```

**Structure Decision**: 仅修改 `src/friday/llm/` 下两个文件，无新建文件。

## 设计方案

### 工具定义（tools.py）

参照现有 `KNOWLEDGE_SEARCH` 的模式，新增 `KNOWLEDGE_ADD`：

- **参数**: `title`（必填，字符串，笔记标题）、`content`（必填，字符串，笔记内容）、`tags`（可选，字符串数组，分类标签）
- **注册**: 添加到 `get_tool_definitions()` 的 tools 列表

### 执行器（executors.py）

参照现有 `_exec_knowledge_search` 的模式，新增 `_exec_knowledge_add`：

1. 提取参数：title、content、tags
2. 校验：title 和 content 不为空，title 超过 100 字符自动截断
3. 调用 `knowledge.adapter.add_note(title, content, tags)` 创建笔记
4. 返回成功结果（包含笔记 ID 和标题）
5. 异常时返回错误信息

### 不改动的部分

- `knowledge/adapter.py` — `add_note` 函数已满足需求，不修改
- `knowledge/store.py`、`fts.py`、`vector.py` — 不涉及
- `cli/display.py`、`cli/repl.py` — 显示和 REPL 逻辑不变
- `llm/agent.py` — Agent 循环逻辑不变，自动识别新工具

## Complexity Tracking

无需记录。无 Constitution 违规。
