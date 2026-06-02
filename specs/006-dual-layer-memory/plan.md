# Implementation Plan: 双层记忆系统

**Branch**: `006-dual-layer-memory` | **Date**: 2026-06-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/006-dual-layer-memory/spec.md`

## Summary

实现双层记忆系统：动态记忆层（Mem0 + ChromaDB 本地向量存储）和结构化文件记忆层（Markdown 文件）。提供统一检索接口，供 LLM 调用层获取上下文。

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: mem0ai（已有依赖）, ChromaDB（Mem0 内置）

**Storage**: Mem0 ChromaDB（`.friday-memory/`）+ Markdown 文件（`.specify/memory/`）

**Testing**: pytest

**Target Platform**: macOS / Linux CLI

**Project Type**: CLI 工具（内部模块）

**Performance Goals**: 记忆添加/检索 < 500ms

**Constraints**: 文件 ≤200 行，函数 ≤30 行，类型注解必须

**Scale/Scope**: 用户记忆量预计 < 1000 条

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | 原则 | 状态 | 说明 |
|---|------|------|------|
| I | 个人化优先 | ✅ | 记忆是个人化的核心基础设施 |
| II | 渐进式学习 | ✅ | 动态记忆自动积累，文件记忆手动沉淀 |
| III | 本地优先 | ✅ | Mem0 + ChromaDB 本地存储 |
| IV | 安全可控 | ✅ | 纯存取模块，无执行能力 |
| V | 简洁实用 | ✅ | Markdown 文件可直接编辑 |
| 边界 | 只管记忆的存取 | ✅ | 不做 LLM 提取，不做 prompt 组装 |

**Gate**: PASS，无违规。

## Project Structure

### Documentation (this feature)

```text
specs/006-dual-layer-memory/
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
src/friday/memory/
├── __init__.py      # 公共 API 导出（~30 行）
├── dynamic.py       # 动态记忆：封装 Mem0（~120 行）
├── files.py         # 文件记忆：constitution/decisions/lessons（~120 行）
└── adapter.py       # 统一接口：两层检索 + CRUD（~100 行）

tests/unit/
├── test_memory_dynamic.py   # 动态记忆测试
└── test_memory_files.py     # 文件记忆测试
```

**Structure Decision**: 4 个源文件，2 个测试文件。与 instruction 模块一致的 adapter 模式。
