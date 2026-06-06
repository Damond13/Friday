# 根因诊断: 知识库启动时未校准离线文件变化

**日期**: 2026-06-06 | **缺陷来源**: [bug-report.md](./bug-report.md)

## 根因分析

### 直接原因

`start_watcher()`（`watcher.py:86`）仅启动 watchdog Observer 监听实时文件事件，没有启动前扫描目录的步骤。`_KnowledgeHandler` 只响应 `on_created`/`on_modified`/`on_deleted` 事件，无法感知历史变化。

关键代码路径：
- `repl.py:71` — `start_watcher()` 启动监控
- `watcher.py:86-96` — 只创建 Observer 并 start，无扫描逻辑
- `watcher.py:28-33` — `on_modified` 只处理触发事件的单个文件

### 根本原因

设计遗漏：知识库索引模块假设文件只会在 Friday 运行期间被修改，忽略了用户可能直接在文件系统中操作 `~/.friday/knowledge/notes/` 目录的场景。只实现了"实时事件驱动"索引，缺少"启动时差异校准"机制。

## 调研发现

### 开源社区同类问题

- [Stack Overflow: Python Watchdog process existing files on startup](https://stackoverflow.com/questions/59265504/python-watchdog-process-existing-files-on-startup) — 确认 watchdog 不支持启动时自动处理已有文件，推荐做法是在启动 Observer 前手动扫描目录并处理
- [Smarter File Watching in Python](https://medium.com/@RampantLions/smarter-file-watching-in-python-rate-limiting-and-change-history-with-watchdog-2114e45e7774) — 建议先快照目录状态，再启动 Observer，对比差异后补处理

### 现有方案对比

| 方案 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| A: 启动全量重建 | 每次启动清空索引，重新扫描全部文件 | 逻辑简单，保证索引与文件完全一致 | 启动慢，文件多时向量化耗时长 |
| B: 启动差异校准 | 对比目录文件与已有索引，只处理差异部分 | 启动快，只处理必要项 | 需要查询已有索引 ID，逻辑稍复杂 |
| C: 启动时 touch 所有文件 | 遍历目录 touch 每个文件触发 watchdog | 改动最小，复用现有逻辑 | 即使未变化也会重新索引，浪费时间 |

## 问题分级

- [X] **代码级 bug** — 现有方案正确，只是缺少启动校准步骤 → 进入 fixplan
- [ ] **方案级问题** — 当前方案选型有根本性缺陷 → 建议转入 SDD 新功能流程重新设计

## 诊断结论

代码级缺陷，watchdog 方案本身合理，只需在 `start_watcher()` 中增加启动校准步骤：对比目录文件（`list_note_files()`）与 FTS 已索引 ID（`SELECT note_id FROM notes_fts`），对缺失的补索引，对文件已删除的清索引。推荐方案 B（差异校准）。
