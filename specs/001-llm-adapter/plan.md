# Implementation Plan: LLM 统一适配层

**Branch**: `001-llm-adapter` | **Date**: 2026-06-01 | **Spec**: [spec.md](spec.md)

## Summary

Friday 的 LLM 统一适配层，基于 OpenAI SDK 实现，通过切换 base_url/api_key 支持智谱和 DeepSeek 双模型。包含 prompt 组装、工具调用定义、流式输出。

核心决策：智谱和 DeepSeek 都 100% 兼容 OpenAI API 格式（包括 function calling 和 streaming），因此只需一个 `openai` SDK 即可统一适配，无需引入 litellm 等重量级库。

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: openai (SDK), pyyaml (配置)

**Storage**: ~/.friday/config.yaml (API Key + 模型配置)

**Testing**: pytest + pytest-mock

**Target Platform**: macOS / Linux CLI

**Project Type**: 内部库模块 (llm/)

**Performance Goals**: 首 token 延迟 < 2s

**Constraints**: 本地运行，不依赖云服务，串行处理

**Scale/Scope**: 单用户个人工具

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原则 | 状态 | 说明 |
|------|------|------|
| I. 个人化优先 | ✅ PASS | prompt 组装支持注入用户记忆和偏好 |
| II. 渐进式学习 | ✅ PASS | MVP 先实现基础调用，后续迭代加工具调用 |
| III. 本地优先 | ✅ PASS | 仅依赖 openai SDK，无云服务 |
| IV. 安全可控 | ✅ PASS | API Key 存本地配置文件，不硬编码 |
| V. 简洁实用 | ✅ PASS | 基于 OpenAI SDK 统一适配，不过度设计 |
| 编码规范 | ✅ PASS | 每文件 < 200 行，类型注解，走 adapter 层 |

**Result**: 全部通过，无违规。

## Project Structure

### Documentation (this feature)

```text
specs/001-llm-adapter/
├── plan.md          # 本文件
├── research.md      # 技术调研
├── data-model.md    # 数据模型
├── quickstart.md    # 快速上手指南
├── contracts/       # 接口契约
└── tasks.md         # 任务列表（由 /speckit.tasks 生成）
```

### Source Code (repository root)

```text
src/friday/llm/
├── __init__.py      # 模块导出
├── adapter.py       # 统一适配器（基于 OpenAI SDK）
├── prompts.py       # System prompt 组装
└── tools.py         # 工具定义（function calling schemas）

tests/unit/
├── test_adapter.py  # 适配器切换 + 错误处理测试
├── test_prompts.py  # prompt 组装测试
└── test_tools.py    # 工具定义验证测试
```

**Structure Decision**: 单项目结构，llm/ 作为 friday 包的子模块。3 个源文件 + 3 个测试文件，符合 < 200 行/文件的约束。
