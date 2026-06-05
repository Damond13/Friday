# Review: 轻量 Embedding 模型切换

**Branch**: `010-lightweight-embedding` | **Reviewer**: Reviewer Agent | **Date**: 2026-06-05

## Summary

将 Embedding 模型从 BAAI/bge-m3（2.1GB, 1024维）切换为 BAAI/bge-small-zh-v1.5（~100MB, 512维）。实际改动 3 行代码（2 个文件）+ 清理旧数据。内存 profiling 结果确认目标达成。

## Checklist

| # | Check Item | Result | Notes |
|---|-----------|--------|-------|
| 1 | Spec compliance (FR-001 ~ FR-006) | ✅ | 见下方详细分析 |
| 2 | Constitution compliance | ✅ | 五项原则均通过 |
| 3 | Architecture compliance | ✅ | 改动限于 knowledge/ 和 memory/，边界清晰 |
| 4 | File size (<=200 lines) | ✅ | embedding.py 45 行，dynamic.py 180 行 |
| 5 | Function size (<=30 lines) | ✅ | 所有函数均在限制内 |
| 6 | Type annotations | ✅ | 类型注解完整 |
| 7 | Adapter layer | ✅ | sentence-transformers 通过 adapter 封装 |
| 8 | Storage layer | ✅ | ChromaDB + Mem0 存储层未变 |
| 9 | Test coverage | ⚠️ | 现有测试覆盖共享模型注入，但见 Important #1 |
| 10 | Security | ✅ | 无安全风险 |
| 11 | No over-engineering | ✅ | 最小化改动，符合预期 |
| 12 | No direct SDK calls | ✅ | 全部走 adapter |

## Spec Compliance Detail

| Requirement | Status | Evidence |
|-------------|--------|----------|
| FR-001 模型切换，权重 < 150MB | ✅ | bge-small-zh-v1.5 模型文件 ~100MB |
| FR-002 内存增量 < 200MB | ✅ | Profiling: RSS 451MB, 增量约 100MB |
| FR-003 集中配置，共享实例 | ✅ | embedding.py 是唯一配置点；dynamic.py 通过 `get_shared_model()` 注入共享实例 |
| FR-004 清空旧 ChromaDB 数据 | ✅ | 已删除 ~/.friday-memory/，新集合自动创建 |
| FR-005 搜索功能正常 | ✅ | tasks.md T007 确认录入+搜索通过 |
| FR-006 清理旧模型缓存 | ✅ | 已删除 models--BAAI--bge-m3/，释放 ~2.1GB |

## Issues

### Important (should fix)

**I-1: `embed_texts` docstring 维度过时**

- File: `src/friday/knowledge/embedding.py`, line 25
- Current: `"""将文本列表转为向量列表（1024 维）"""`
- Should be: `"""将文本列表转为向量列表（512 维）"""` 或动态引用 `_EMBEDDING_DIM`
- Impact: 误导开发者，以为向量维度仍是 1024

### Suggestions (nice to have)

**S-1: 测试中硬编码维度 `_DIM = 1024`**

- File: `tests/unit/test_vector.py`, line 11
- 测试 mock 了 `embed_text`，所以 1024 不会导致测试失败，但作为维护隐患：如果后续有人移除 mock 或基于此值写新测试，会遇到维度不匹配
- 建议: 改为 `from friday.knowledge.embedding import get_embedding_dim` 并使用 `_DIM = get_embedding_dim()`，或者在 mock 上下文中改为 512

**S-2: 模型名称两处硬编码**

- `src/friday/knowledge/embedding.py` line 13: `_MODEL_NAME = "BAAI/bge-small-zh-v1.5"`
- `src/friday/memory/dynamic.py` line 60: `"model": "BAAI/bge-small-zh-v1.5"`
- 当前不影响功能（dynamic.py 的字符串仅用于 Mem0 初始配置，随后被共享实例替换），但若未来再切换模型需要改两个地方
- 建议: dynamic.py 直接 import `_MODEL_NAME` 或不做改动（风险低，改动频率极低）

## Verdict

**审核通过**

改动精准、范围最小化、spec 六项功能需求全部满足、内存 profiling 数据确认目标达成。仅需修复一个 docstring 维度数字（I-1），无 blocking issue。
