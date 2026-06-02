# Implementation Plan: 指令学习模块

**Branch**: `005-instruction-learning` | **Date**: 2026-06-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/005-instruction-learning/spec.md`

## Summary

实现指令学习模块，支持用户通过结构化数据创建指令、以 YAML 文件存储、提供精确+关键词两级匹配、以及增删改查管理。模块只负责存储和匹配，不执行命令。

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: PyYAML（已有依赖，config.py 使用）

**Storage**: YAML 文件（`~/.friday/instructions/`，每条指令一个文件）

**Testing**: pytest

**Target Platform**: macOS / Linux CLI

**Project Type**: CLI 工具（内部模块）

**Performance Goals**: 50 条指令内匹配 < 100ms

**Constraints**: 文件 ≤200 行，函数 ≤30 行，类型注解必须

**Scale/Scope**: 预计用户指令量 < 200 条

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | 原则 | 状态 | 说明 |
|---|------|------|------|
| I | 个人化优先 | ✅ | 指令完全由用户定义，深度个人化 |
| II | 渐进式学习 | ✅ | 对话式教学，从单步到多步渐进 |
| III | 本地优先 | ✅ | YAML 文件存储，人可读可编辑 |
| IV | 安全可控 | ✅ | 只存储和匹配，不执行命令 |
| V | 简洁实用 | ✅ | YAML 直编，简单高效 |
| 边界 | 只管存储和匹配 | ✅ | 不执行，不调 LLM，不做 UI |

**Gate**: PASS，无违规。

## Project Structure

### Documentation (this feature)

```text
specs/005-instruction-learning/
├── spec.md
├── plan.md              # 本文件
├── research.md          # 技术决策
├── data-model.md        # 数据模型
├── quickstart.md        # 验证场景
├── contracts/           # API 合约
└── tasks.md             # 任务列表（/speckit.tasks 生成）
```

### Source Code (repository root)

```text
src/friday/instruction/
├── __init__.py      # 公共 API 导出（~30 行）
├── models.py        # Instruction/Action/MatchResult 数据类（~70 行）
├── store.py         # YAML 存储：加载/保存/删除/列表（~120 行）
├── matcher.py       # 匹配引擎：精确+关键词（~80 行）
└── adapter.py       # 统一接口：teach/match/list/delete（~100 行）

tests/unit/
├── test_instruction_store.py    # 存储测试
└── test_instruction_matcher.py  # 匹配测试
```

**Structure Decision**: 单模块结构，5 个源文件，2 个测试文件。与 executor 模块一致的 adapter 模式。
