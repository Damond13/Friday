# 根因诊断: jieba 分词库 stdout 输出污染终端显示

**日期**: 2026-06-07 | **缺陷来源**: [bug-report.md](./bug-report.md)

## 根因分析

### 直接原因

`src/friday/knowledge/fts.py:6` 在模块顶层 `import jieba`，jieba 使用 Python `logging` 模块输出日志，其默认日志级别为 `logging.DEBUG`。当 `fts.py:77` 的 `_tokenize()` 首次调用 `jieba.cut_for_search()` 时，jieba 触发延迟初始化，向 stdout 输出 INFO 级别的加载日志：
```
Loading model from cache /var/folders/...
Loading model cost 0.258 seconds.
Prefix dict has been built successfully.
```
这些日志绕过了 Rich Console，直接写入终端，破坏了 `repl.py:106` 的 `console.status()` spinner 动画和 Rich 的光标位置追踪。

### 根本原因

开发 `knowledge/fts.py` 时未考虑 jieba 日志输出对交互模式终端显示的影响。jieba 的日志污染是已知问题（GitHub issues #569），社区已提供官方解决方案 `jieba.setLogLevel()`，但代码中未使用。

### 同类风险

以下库也有潜在的 stdout/stderr 污染风险：
- `sentence_transformers`（`embedding.py:20`）— 已通过 `HF_HUB_OFFLINE=1` 缓解
- `chromadb`（`vector.py:6`）— 无抑制措施，但目前未观察到污染
- `mem0`（`memory/dynamic.py:74`）— 已通过 `MEM0_TELEMETRY=False` 缓解

## 调研发现

### 开源社区同类问题

| 来源 | 内容 |
|------|------|
| [jieba#569](https://github.com/fxsjy/jieba/issues/569) | 请求添加 silent flag，官方推荐 `jieba.setLogLevel()` |
| [jieba#529](https://github.com/fxsjy/jieba/issues/529) | 同类问题，社区建议设置 logger 级别 |
| [StackOverflow](https://stackoverflow.com/questions/6796492/temporarily-redirect-stdout-stderr) | `contextlib.redirect_stdout` 方案，但不适用于库代码 |

### 现有方案对比

| 方案 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| `jieba.setLogLevel(logging.WARNING)` | jieba 官方 API，一行代码 | 最简洁，只抑制 jieba 日志，不影响其他输出 | 仅解决 jieba，不通用 |
| `contextlib.redirect_stdout` | Python 内置上下文管理器 | 通用方案 | 不适用于库代码和线程环境 |
| 文件描述符重定向 | OS 级别重定向 | 可捕获 C 层输出 | 过于复杂，杀鸡用牛刀 |

**推荐方案**: `jieba.setLogLevel(logging.WARNING)` — 最简洁、官方推荐、最小改动。

## 问题分级

- [x] **代码级 bug** — 现有方案正确，只是实现有缺陷 → 进入 fixplan
- [ ] **方案级问题** — 当前方案选型有根本性缺陷 → 建议转入 SDD 新功能流程重新设计

## 诊断结论

jieba 日志级别未设置导致加载信息污染终端，通过在 `fts.py` 中添加一行 `jieba.setLogLevel(logging.WARNING)` 即可修复。
