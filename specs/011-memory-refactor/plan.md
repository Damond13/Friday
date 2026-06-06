# Implementation Plan: Friday 记忆系统重构

**Branch**: `011-memory-refactor` | **Date**: 2026-06-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/011-memory-refactor/spec.md`

## Summary

重构 Friday 的记忆系统，明确其定位为 Friday 与用户对话交互的功能。具体改动：移除文件记忆层（`memory/files.py`），简化 `memory/adapter.py` 为只代理动态记忆，将动态记忆存储路径从 `~/.friday-memory/` 改到 `~/.friday/memory/`，改进 `_build_context()` 用用户当前消息内容作为检索关键词替代硬编码的"用户偏好 习惯 设置"。

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: Mem0（动态记忆管理）、ChromaDB（向量存储，Mem0 内部使用）、sentence-transformers（embedding）

**Storage**: ChromaDB 持久化存储（由 Mem0 管理），当前路径 `~/.friday-memory/`，迁移到 `~/.friday/memory/`

**Testing**: pytest

**Target Platform**: macOS / Linux CLI

**Project Type**: CLI 工具

**Performance Goals**: 记忆检索每次对话触发一次，不影响对话响应速度

**Constraints**: 记忆系统初始化失败时必须降级运行，不影响基本对话

**Scale/Scope**: 单用户本地使用，记忆条目预计百级别

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原则 | 状态 | 说明 |
|------|------|------|
| I. 个人化优先 | PASS | 重构核心目标就是让记忆系统更好地服务个人化 |
| II. 渐进式学习 | PASS | 动态记忆自动提取符合渐进式学习理念 |
| III. 本地优先 | PASS | 数据仍在本地，只是调整路径 |
| IV. 安全可控 | PASS | 不涉及执行器变更 |
| V. 简洁实用 | PASS | 移除文件记忆简化了系统 |
| 技术栈约束 | PASS | 继续使用 Mem0 + ChromaDB |
| 编码规范 | PASS | 文件≤200行，函数≤30行，类型注解 |
| 模块边界 | PASS | memory/ 只管记忆存取，职责不变 |
| 测试执行规范 | PASS | 遵守测试策略 |

**Gate Result**: PASS — 无违规

## Project Structure

### Documentation (this feature)

```text
specs/011-memory-refactor/
├── plan.md              # 本文件
├── spec.md              # 功能规格
├── checklists/          # 质量检查清单
└── tasks.md             # 任务列表（/speckit.tasks 生成）
```

### Source Code (repository root)

```text
src/friday/
├── memory/
│   ├── __init__.py      # 模块导出（需更新）
│   ├── adapter.py       # 统一接口（需精简：移除 files 相关导入和函数）
│   ├── dynamic.py       # 动态记忆（需修改：MEMORY_DIR 路径 + search_memory 返回类型修复）
│   └── files.py         # 文件记忆（需删除）
├── cli/
│   └── repl.py          # REPL（需修改：_build_context 用用户消息内容检索）
├── llm/
│   └── prompts.py       # PromptContext（无需改动，已支持 user_memories）
└── config.py            # 配置（无需改动，CONFIG_DIR 已定义）

tests/
├── unit/
│   └── test_memory.py   # 记忆模块单元测试（需更新/新增）
└── integration/
    └── test_memory_integration.py  # 集成测试（需新增）
```

**Structure Decision**: 在现有 `src/friday/memory/` 目录上修改，不新增目录。删除 `files.py`，精简 `adapter.py`，修改 `dynamic.py` 和 `repl.py`。

## 改动清单

### 1. 删除 `src/friday/memory/files.py`

整个文件删除。这个文件实现了文件记忆（决策记录、经验教训、项目宪法），属于开发流程，不属于 Friday 用户功能。

### 2. 精简 `src/friday/memory/adapter.py`

当前文件同时代理动态记忆和文件记忆。重构后只代理动态记忆：

- 移除所有 `files.py` 的导入和转发函数（`add_decision`, `list_decisions`, `add_lesson`, `list_lessons`, `get_constitution`）
- 移除 `_search_files` 的调用
- `search_memories()` 简化为只调用 `_search_dynamic()`
- 保留 `add_memory()`, `search_memories()`, `list_memories()`, `delete_memory()` 四个函数

### 3. 修改 `src/friday/memory/dynamic.py` — 存储路径

将 `MEMORY_DIR` 从 `CONFIG_DIR.parent / ".friday-memory"` 改为 `CONFIG_DIR / "memory"`，即从 `~/.friday-memory/` 改为 `~/.friday/memory/`。

### 4. 修改 `src/friday/memory/dynamic.py` — search_memory 返回类型

当前 `search_memory()` 返回 `list[MemorySearchResult]`，但 `_build_context()` 中用了 `r["memory"]` 字典访问（与 `MemorySearchResult` dataclass 不匹配）。需要统一接口。

### 5. 修改 `src/friday/cli/repl.py` — `_build_context()`

当前实现问题：
- 用硬编码关键词"用户偏好 习惯 设置"检索记忆
- 用 stderr 重定向的方式抑制 Mem0 的 jieba 日志（hack）

重构为：
- 使用用户当前消息（`session.messages[-1].content`）作为检索查询
- 限制注入记忆条数（上限 5 条）
- 移除 stderr hack，改为在 logging 层面抑制

### 6. 更新 `src/friday/memory/__init__.py`

移除 `files.py` 相关的导出，只导出 `adapter.py` 的函数。

### 7. 更新 `src/friday/cli/repl.py` — `_try_quick_note()`

当前 `_try_quick_note()` 中直接调用 `knowledge.adapter.add_note()`，这个逻辑不涉及记忆系统，无需修改。确认无影响。

### 8. 更新 CLAUDE.md

- 移除"双层记忆系统"相关描述，改为"动态记忆系统"
- 更新架构图中 memory/ 的描述
- 移除文件记忆相关的目录说明

## 不改动的部分

- `src/friday/llm/prompts.py` — `PromptContext` 和 `build_system_prompt` 已经支持 `user_memories`，无需改动
- `src/friday/llm/agent.py` — `run_agent_loop` 已正确传递 context，无需改动
- `src/friday/knowledge/` — 知识库模块独立于记忆系统，不受影响
- `src/friday/llm/tools.py` — 当前无记忆相关工具，暂不新增（spec 中暂不开放用户主动管理记忆）
- `src/friday/config.py` — `CONFIG_DIR` 定义不需要改，`MEMORY_DIR` 在 `dynamic.py` 中改

## Complexity Tracking

无 Constitution 违规，不需要填写。
