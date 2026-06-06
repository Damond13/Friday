# 修复方案: 嵌入模型重复加载且延迟到首次交互时初始化

**日期**: 2026-06-06 | **缺陷来源**: [bug-report.md](./bug-report.md) | **诊断依据**: [diagnosis.md](./diagnosis.md)

## 修复策略

在 `run_repl()` 的 `start_watcher()` 之后，主动调用 `_get_memory()` 触发 Mem0 预初始化，将模型加载从用户首次交互时移到启动阶段。

## 长期影响评估

### 可扩展性

无影响。仅调整初始化时机，不改变模块接口。

### 未来功能影响

正面：未来如有其他启动时需要预初始化的模块，可复用同一位置。

### 风险

- Mem0 初始化失败时不影响启动（`_get_memory()` 内部已 catch 异常返回 None）
- 启动时间增加约 1-2 秒（Mem0 模型加载），但用户不再在首次交互时感知延迟

## 改动清单

| 文件 | 改动内容 | 原因 |
|------|---------|------|
| `src/friday/cli/repl.py` | 在 `start_watcher()` 之后添加 `from friday.memory.dynamic import _get_memory; _get_memory()` | 启动阶段预初始化 Mem0 |

## 不改动的部分

- `src/friday/memory/dynamic.py` — 初始化逻辑不变，只是调用时机提前
- `src/friday/knowledge/embedding.py` — 共享模型逻辑不变
- 所有其他文件

## 测试更新评估

- **已有测试文件**: `tests/unit/test_memory_dynamic.py`、`tests/unit/test_memory_context.py`
- **需要更新的测试**: 无。改动仅在 CLI 层（`repl.py`），CLAUDE.md 明确"CLI 层不写测试"。现有测试 mock 了 `_get_memory`，不受影响。
- **测试命令**: 无需运行

## 验证方案

1. 启动 Friday，观察日志中 `Loading weights` 在 `Friday>` 提示符出现前完成
2. 发送"你好"，确认无 FutureWarning 和额外加载延迟
