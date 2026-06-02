# 实现计划：执行器模块

**Branch**: `004-executor` | **Date**: 2026-06-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-executor/spec.md`

## 概要

执行器模块是 Friday 的命令执行核心，负责运行 Shell 命令、分级安全管理（安全/新指令/危险三级策略）、超时控制和输出处理。使用 `asyncio.create_subprocess_shell` 执行命令、SQLite 存储执行历史和安全策略、已有的 `llm/adapter.py` 做输出摘要。

## 技术上下文

**Language/Version**: Python 3.13

**Primary Dependencies**: asyncio（标准库）, aiosignal（信号处理）, 已有 llm/adapter.py（输出摘要）

**Storage**: SQLite（执行历史 + 安全策略 + 用户信任）

**Testing**: pytest + pytest-asyncio

**Target Platform**: 本地 CLI（macOS / Linux）

**Project Type**: CLI 工具模块

**Performance Goals**: 安全命令 < 1s 响应，超时控制精度 ±1s

**Constraints**: 无沙箱隔离，直接执行本地 Shell

**Scale/Scope**: 单用户，串行执行

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原则 | 状态 | 说明 |
|------|------|------|
| I. 个人化优先 | PASS | 用户可自定义安全策略，记住信任偏好 |
| II. 渐进式学习 | PASS | 新指令首次确认后可记住 |
| III. 本地优先 | PASS | 全部本地执行，无外部依赖 |
| IV. 安全可控 | PASS | 三级安全策略是核心设计，直接对应宪法要求 |
| V. 简洁实用 | PASS | 短输出直显，长输出摘要 |
| 编码规范 | PASS | 文件 < 200 行，函数 < 30 行，adapter 层 |
| 模块边界 | PASS | executor/ 只管执行命令和安全管理，不关心为什么执行 |

## Project Structure

### Documentation (this feature)

```text
specs/004-executor/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── executor-api.md
└── tasks.md
```

### Source Code (repository root)

```text
src/friday/executor/
├── __init__.py          # 公共 API 导出
├── runner.py            # 命令执行引擎（subprocess 封装）
├── safety.py            # 安全策略管理（三级分类 + 黑白名单）
├── output.py            # 输出处理（长输出摘要 + 流式输出）
├── history.py           # 执行历史记录（SQLite 存储）
└── adapter.py           # 统一执行接口（上层调用入口）

tests/
├── unit/
│   ├── test_runner.py
│   ├── test_safety.py
│   ├── test_output.py
│   └── test_history.py
└── conftest.py
```

**Structure Decision**: 单项目结构，executor/ 作为独立模块，通过 adapter.py 对外暴露统一接口。runner.py 是执行核心，safety.py 负责安全策略，output.py 负责输出处理，history.py 负责历史记录。

## Complexity Tracking

无宪法违规，无需记录。
