# 修复方案: jieba 分词库 stdout 输出污染终端显示

**日期**: 2026-06-07 | **缺陷来源**: [bug-report.md](./bug-report.md) | **诊断依据**: [diagnosis.md](./diagnosis.md)

## 修复策略

在 `fts.py` 中 `import jieba` 之后立即调用 `jieba.setLogLevel(logging.WARNING)`，抑制 jieba 加载时的 INFO 级别日志输出。这是 jieba 官方推荐的方案，一行代码解决问题。

## 长期影响评估

### 可扩展性

中性。改动不影响模块的扩展能力，也不增加复杂度。

### 未来功能影响

正面。未来任何使用 `fts.py` 的地方都不会再被 jieba 日志干扰，无需在每个调用点单独处理。

### 风险

极低。`setLogLevel` 是 jieba 官方 API，不影响分词功能和性能，仅抑制日志输出。

## 改动清单

| 文件 | 改动内容 | 原因 |
|------|---------|------|
| `src/friday/knowledge/fts.py` | 在 `import jieba` 后添加 `import logging` 和 `jieba.setLogLevel(logging.WARNING)` | 抑制 jieba 加载日志 |

## 不改动的部分

- `src/friday/cli/repl.py` — spinner 逻辑不变
- `src/friday/cli/display.py` — 显示函数不变
- `src/friday/knowledge/` 其他文件 — 不涉及
- `src/friday/memory/` — 不涉及
- 不引入新的依赖或抽象

## 测试更新评估

- **已有测试文件**: `tests/unit/test_fts.py`（10 个测试用例）
- **需要更新的测试**: 在 `tests/unit/test_fts.py` 中新增一个测试用例，验证导入 `fts` 模块后 jieba 日志级别为 WARNING
- **测试命令**: `pytest tests/unit/test_fts.py -v`

## 验证方案

1. 运行 `pytest tests/unit/test_fts.py -v` 确认测试通过
2. 启动 Friday 交互模式，发送触发知识库检索的消息，确认终端无 jieba 日志输出
