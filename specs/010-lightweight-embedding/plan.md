# Implementation Plan: 轻量 Embedding 模型切换

**Branch**: `010-lightweight-embedding` | **Date**: 2026-06-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/010-lightweight-embedding/spec.md`

## Summary

将 Friday 的 Embedding 模型从 BAAI/bge-m3（2.1GB，1024维）切换为 BAAI/bge-small-zh-v1.5（~100MB，512维），内存占用从 ~6GB 降至 ~300MB。历史数据直接丢弃，不迁移。

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: sentence-transformers, chromadb, mem0

**Storage**: ChromaDB（旧数据清空，新集合自动创建）

**Testing**: 手动验证 + 内存测量脚本

**Target Platform**: macOS 本地 CLI

**Project Type**: 性能优化

**Performance Goals**: embedding 模型内存增量 < 200MB

**Constraints**: 改动范围 2 个源文件

**Scale/Scope**: 2 行配置修改 + 清理旧数据 + 清理旧缓存

## Constitution Check

| 原则 | 状态 | 评估 |
|------|------|------|
| I. 个人化优先 | PASS | 更轻量让 Friday 在资源受限时也能运行 |
| II. 渐进式学习 | PASS | 不影响学习机制 |
| III. 本地优先 | PASS | 仍用本地模型 |
| IV. 安全可控 | PASS | 用户确认数据可丢弃 |
| V. 简洁实用 | PASS | 100MB 比 2.1GB 更简洁 |

**Result**: PASS

## Project Structure

```text
src/friday/knowledge/
└── embedding.py        # [修改] 模型名 + 维度（2行）

src/friday/memory/
└── dynamic.py          # [修改] Mem0 embedder 模型名（1行）

~/.friday-memory/       # [清空] 旧 ChromaDB 数据
~/.friday/indexes/      # [清空] 旧知识库向量索引
~/.cache/huggingface/   # [清理] 旧 bge-m3 缓存（2.1GB）
```
