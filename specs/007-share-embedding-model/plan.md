# Implementation Plan: 共享 Embedding 模型实例

**Branch**: `007-share-embedding-model` | **Date**: 2026-06-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/007-share-embedding-model/spec.md`

## Summary

知识库模块和动态记忆模块各自加载 BAAI/bge-m3 嵌入模型（~2GB），合计占用 ~4GB 内存。通过在 knowledge/embedding.py 导出共享模型获取函数，并在 Mem0 初始化后替换其内部模型为共享实例，将内存占用降至 ~2GB。

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: sentence-transformers (BAAI/bge-m3), mem0ai, chromadb

**Storage**: ChromaDB (向量存储), SQLite (FTS5 全文索引)

**Testing**: pytest (260 个现有测试)

**Target Platform**: macOS / Linux 本地 CLI

**Project Type**: CLI 工具

**Performance Goals**: 嵌入模型内存占用减半（4GB → 2GB）

**Constraints**: 离线模式运行（HF_HUB_OFFLINE=1），不下载额外模型

**Scale/Scope**: 单用户本地工具，影响 2 个源文件 + 1 个测试文件

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原则 | 状态 | 说明 |
|------|------|------|
| I. 个人化优先 | PASS | 不影响用户交互和个性化功能 |
| II. 渐进式学习 | PASS | 不影响指令学习和知识积累 |
| III. 本地优先 | PASS | 减少本地资源占用，符合本地优先理念 |
| IV. 安全可控 | PASS | 不涉及执行器或安全策略变更 |
| V. 简洁实用 | PASS | 更简洁的资源管理方式 |
| 模块边界 | WATCH | memory/ 需从 knowledge/ 导入共享模型函数，产生 memory → knowledge 依赖 |

**模块边界评估**：memory/ 依赖 knowledge/embedding.py 的 `get_shared_model()` 函数。embedding.py 本质上是嵌入模型的 adapter 层，服务多个消费者是合理的。此依赖仅为获取模型实例，不涉及知识库业务逻辑，可接受。

## Project Structure

### Documentation (this feature)

```text
specs/007-share-embedding-model/
├── spec.md              # 功能规格
├── plan.md              # 本文件
├── research.md          # Phase 0 技术调研
├── quickstart.md        # 验证步骤
└── checklists/
    └── requirements.md  # 质量检查清单
```

### Source Code (repository root)

```text
src/friday/
├── knowledge/
│   ├── embedding.py     # 修改：导出 get_shared_model()
│   └── ...
├── memory/
│   ├── dynamic.py       # 修改：注入共享模型到 Mem0
│   └── ...
└── ...

tests/
├── unit/
│   └── test_memory_dynamic.py  # 可能需更新 mock
└── integration/
    └── test_memory_integration.py  # 可能需更新 mock
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| memory → knowledge 依赖 | 共享嵌入模型实例以节省 2GB 内存 | 将 embedding 抽到独立公共模块会引入更多文件和导入链，对小优化来说过度设计 |
