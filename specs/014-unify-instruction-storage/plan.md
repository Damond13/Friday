# Implementation Plan: 指令系统存储统一到知识库

**Branch**: `014-unify-instruction-storage` | **Date**: 2026-06-08 | **Spec**: [spec.md](./spec.md)

## Summary

将指令系统的检索能力升级为语义检索（复用知识库的 FTS + ChromaDB），同时保留 YAML 存储格式（结构化数据不适合塞进 Markdown）。指令和知识共享索引层，但通过 `type` 元数据字段严格区分。新增 4 个 LLM 工具（`instruction_add`、`instruction_search`、`instruction_list`、`instruction_delete`），复用现有 `instruction/adapter.py` 的 CRUD 逻辑。

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: 无新依赖，复用现有 knowledge（FTS5 + ChromaDB）和 instruction 模块

**Storage**: 指令保持 YAML 格式（`~/.friday/instructions/`），索引共享知识库的 FTS + ChromaDB

**Testing**: pytest

**Target Platform**: macOS Terminal / iTerm2 / VS Code 终端

**Project Type**: CLI 工具

**Performance Goals**: 指令检索 < 1 秒

**Constraints**: 不引入新依赖；共享索引但存储格式分离

**Scale/Scope**: 单用户 CLI，指令数量预计 < 100 条

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原则 | 状态 | 说明 |
|------|------|------|
| I. 个人化优先 | ✅ 通过 | 指令学习是核心个人化能力，语义检索大幅提升匹配能力 |
| II. 渐进式学习 | ✅ 通过 | 对话式教会指令，与现有教学模式一致 |
| III. 本地优先 | ✅ 通过 | 所有数据存储在本地 |
| IV. 安全可控 | ✅ 通过 | 指令执行走现有执行器安全策略（FR-006） |
| V. 简洁实用 | ✅ 通过 | 复用现有模块，最小改动 |
| 模块边界 - knowledge/ | ✅ 通过 | 共享 FTS + ChromaDB 索引，通过 type 字段区分 |
| 模块边界 - instruction/ | ✅ 通过 | 保留 YAML 存储，adapter 层新增索引操作 |
| 模块边界 - llm/ | ✅ 通过 | 新增工具定义和执行器 |
| 编码规范 - 200行/30行 | ✅ 通过 | 预计每个文件增加 < 30 行 |
| 编码规范 - adapter 层 | ✅ 通过 | instruction/adapter.py 调用 knowledge 索引层 |

**Gate Result**: PASS — 所有原则合规，无违规。

## 设计方案

### 核心设计决策：共享索引，独立存储

**为什么不把指令转成 Markdown 笔记？**

1. 指令有结构化数据（触发词、动作列表、确认策略），塞进 YAML frontmatter 会很别扭且难以维护
2. 动作列表是嵌套结构（command + description + confirm），Markdown frontmatter 的简单键值对无法优雅表达
3. YAML 格式人可读、可直接编辑，这是 Open Interpreter 等工具也采用的方式
4. 用户的"知识是知识，指令是指令"原则在存储层面也应体现

**方案**：指令保持 YAML 文件存储，但 FTS 和 ChromaDB 索引中增加 `type` 字段区分类型。检索时通过 `type` 过滤实现知识/指令互不干扰。

### 索引层改动（knowledge/）

#### FTS5（fts.py）

- `notes_fts` 表新增 `type` 列（默认 `"note"`）
- `notes_fts_index` FTS 虚拟表同步增加 `type` 字段
- `insert()` 函数增加 `entry_type` 参数（默认 `"note"`）
- `search()` 函数增加 `entry_type` 过滤参数（可选）
- 数据库迁移：`ALTER TABLE notes_fts ADD COLUMN type TEXT DEFAULT 'note'`

#### ChromaDB（vector.py）

- `upsert()` 函数的 metadata 增加 `type` 字段（默认 `"note"`）
- `search()` 函数增加 `entry_type` 过滤参数，使用 ChromaDB `where` 过滤

#### 知识适配器（knowledge/adapter.py）

- 现有 `add_note()` / `search()` 等函数保持不变，默认 `type="note"`
- 新增 `index_instruction()` 函数，供 instruction/adapter 调用，写入 `type="instruction"` 的索引
- 新增 `search_instructions()` 函数，按 `type="instruction"` 过滤检索
- 新增 `delete_instruction_index()` 函数

### 指令层改动（instruction/）

#### 适配器（instruction/adapter.py）

- `teach()` 函数：创建指令后调用 `knowledge.adapter.index_instruction()` 建立索引
- `remove()` 函数：删除指令后调用 `knowledge.adapter.delete_instruction_index()` 清除索引
- `match()` 函数：改为调用 `knowledge.adapter.search_instructions()`，用语义检索替代纯文本规则匹配
- 新增 `list_instructions()` → 已存在，无需改动
- 新增 `search_instructions()` 函数：对外暴露，供 LLM 工具调用

### LLM 工具层改动（llm/）

#### 工具定义（tools.py）

新增 4 个工具定义：

| 工具名 | 必填参数 | 可选参数 | 说明 |
|--------|---------|---------|------|
| `instruction_add` | trigger, actions | name, keywords, type | 创建/更新指令 |
| `instruction_search` | query | limit | 语义检索指令 |
| `instruction_list` | — | — | 列出所有指令 |
| `instruction_delete` | name | — | 删除指定指令 |

#### 执行器（executors.py）

新增 4 个执行器函数，对应上述工具。每个执行器调用 `instruction/adapter.py` 的对应函数。

### 不改动的部分

- `knowledge/store.py` — Note 数据模型和文件管理不变
- `instruction/models.py` — Instruction / Action 数据模型不变
- `instruction/store.py` — YAML 文件读写不变
- `instruction/matcher.py` — 保留但不再被主流程调用
- `cli/display.py`、`cli/repl.py` — 显示和 REPL 逻辑不变
- `llm/agent.py` — Agent 循环逻辑不变，自动识别新工具

## Project Structure

### Documentation (this feature)

```text
specs/014-unify-instruction-storage/
├── spec.md              # 功能规格
├── plan.md              # 本文件
├── research.md          # 调研报告
└── tasks.md             # 任务列表（/speckit.tasks 生成）
```

### Source Code (repository root)

```text
src/friday/
├── knowledge/
│   ├── fts.py           # 修改：新增 type 列和过滤参数
│   ├── vector.py        # 修改：metadata 增加 type，search 增加过滤
│   └── adapter.py       # 修改：新增 instruction 相关索引函数
├── instruction/
│   ├── adapter.py       # 修改：teach/remove 改为调 knowledge 索引，match 改用语义检索
│   ├── matcher.py       # 不改动（保留，不再被主流程调用）
│   ├── models.py        # 不改动
│   └── store.py         # 不改动
└── llm/
    ├── tools.py         # 修改：新增 4 个指令工具定义
    └── executors.py     # 修改：新增 4 个指令执行器
```

**Structure Decision**: 仅修改 `knowledge/`、`instruction/`、`llm/` 下的现有文件，无新建文件。

## Complexity Tracking

无需记录。无 Constitution 违规。
