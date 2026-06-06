# 修复方案: 知识库启动时未校准离线文件变化

**日期**: 2026-06-06 | **缺陷来源**: [bug-report.md](./bug-report.md) | **诊断依据**: [diagnosis.md](./diagnosis.md)

## 修复策略

在 `start_watcher()` 启动 Observer 之前，增加差异校准步骤 `reconcile()`：扫描目录文件与已有 FTS 索引的差异，覆盖三种情况——新增文件补索引、修改文件重建索引、删除文件清索引。通过在 FTS 表中存储文件 mtime 实现修改检测。

## 长期影响评估

### 可扩展性

`reconcile()` 作为独立函数，未来可被斜杠命令（如 `/rebuild`）直接复用，支持手动触发全量校准。

### 未来功能影响

正面：为未来的索引管理命令提供基础。不阻碍任何已规划功能。

### 风险

- 离线积累大量文件时首次校准有向量化开销，但这是用户期望行为，且只处理差异部分。
- `mtime` 列新增到 FTS 表，已有数据 mtime 默认为 0，首次 reconcile 会视为"已修改"触发重建，保证数据一致性。

## 改动清单

| 文件 | 改动内容 | 原因 |
|------|---------|------|
| `src/friday/knowledge/fts.py` | `notes_fts` 表新增 `mtime REAL DEFAULT 0` 列；`insert()` 增加 `mtime` 参数并存储；新增 `get_all_index_mtimes(conn)` 函数返回 `{note_id: mtime}` 字典 | 存储文件修改时间，支持修改检测和差异对比 |
| `src/friday/knowledge/adapter.py` | `index_note()` 获取文件 mtime 并传给 `fts_insert()` | 衔接 mtime 采集 |
| `src/friday/knowledge/watcher.py` | 新增 `reconcile()` 函数：对比目录文件 mtime 与 FTS 存储 mtime，处理新增/修改/删除；在 `start_watcher()` 中 Observer start 前调用 | 核心修复：启动校准 |
| `tests/unit/test_fts.py` | 新增 `TestGetAllIndexMtimes` 测试类：空库、有数据、mtime 存储与读取 | 测试新增函数 |
| `tests/unit/test_watcher.py` | 新增 `TestReconcile` 测试类：无差异、新增文件、修改文件、删除文件、start_watcher 触发 reconcile | 测试核心修复逻辑 |

### reconcile 处理逻辑

```
1. 扫描目录：list_note_files() → {note_id: file_mtime}
2. 查询索引：get_all_index_mtimes() → {note_id: stored_mtime}
3. 差异对比：
   - 文件有但索引没有（新增）→ _index_file()
   - 文件有且索引有，但 mtime 不同（修改）→ _reindex_file()
   - 索引有但文件没有（删除）→ adapter.delete_note()
```

## 不改动的部分

- `src/friday/knowledge/store.py` — 已有 `list_note_files()`，无需改动
- `src/friday/knowledge/vector.py` — 向量索引的增删通过 `index_note()` 和 `adapter.delete_note()` 间接处理，无需改动
- `src/friday/cli/repl.py` — `start_watcher()` 调用签名不变，无需改动

## 测试更新评估

- **已有测试文件**:
  - `tests/unit/test_fts.py`（FTS 单元测试，7 个用例）
  - `tests/unit/test_watcher.py`（watcher 单元测试，6 个用例）
- **需要更新的测试**:
  - `tests/unit/test_fts.py`:
    - `TestFTS` 中 `insert` 调用需加上 `mtime` 参数
    - 新增 `TestGetAllIndexMtimes` 测试类：空库返回空字典、插入后返回正确 mtime
    - 新增 `test_insert_stores_mtime`：验证 mtime 被正确存储
  - `tests/unit/test_watcher.py`:
    - 新增 `TestReconcile` 测试类：
      - `test_no_diff_no_action` — 无差异时不调用索引函数
      - `test_new_file_gets_indexed` — 有新增文件时调用 `_index_file`
      - `test_modified_file_gets_reindexed` — mtime 变化时调用 `_reindex_file`
      - `test_deleted_file_gets_cleaned` — 孤立索引时调用 `delete_note`
      - `test_start_watcher_calls_reconcile` — 验证 `start_watcher` 触发 `reconcile`
- **需要删除的测试**: 无
- **测试命令**:
  - `pytest tests/unit/test_fts.py -v`
  - `pytest tests/unit/test_watcher.py -v`

## 验证方案

1. 运行 `pytest tests/unit/test_fts.py tests/unit/test_watcher.py -v` 确认测试通过
2. 关闭 Friday → 在 `~/.friday/knowledge/notes/` 新增 .md 文件 → 启动 Friday → 搜索新增内容，确认可检索
3. 关闭 Friday → 修改已有 .md 文件内容 → 启动 Friday → 搜索修改后的内容，确认索引已更新
