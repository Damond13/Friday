# 验证报告: 知识库启动时未校准离线文件变化

**日期**: 2026-06-06 | **缺陷来源**: [bug-report.md](./bug-report.md) | **修复方案**: [fixplan.md](./fixplan.md)

## 验证环境

- **操作系统**: macOS Darwin 24.5.0
- **Python**: 3.13.7
- **Friday**: main 分支（未提交的工作区改动）

## 修复有效性

### 复现步骤验证

| 步骤 | 预期 | 实际 |
|------|------|------|
| 1. `start_watcher()` 调用 `reconcile()` | 在 Observer 启动前执行校准 | ✅ watcher.py:125 调用 reconcile() |
| 2. reconcile 检测新增文件 | 文件不在索引中时调用 `_index_file()` | ✅ watcher.py:65-67 |
| 3. reconcile 检测修改文件 | mtime 不同时调用 `_reindex_file()` | ✅ watcher.py:68-70 |
| 4. reconcile 清理孤立索引 | 索引有但文件没有时调用 `delete_note()` | ✅ watcher.py:71-77 |
| 5. mtime 存储和查询 | FTS 表存储 mtime，可查询 | ✅ fts.py:19 新增列，fts.py:130-133 查询函数 |

### 端到端逻辑验证

启动流程：`start_watcher()` → `reconcile()` → 扫描目录 + 对比索引 → 处理差异 → 启动 Observer。覆盖了 bug-report 中描述的三种离线场景（新增/修改/删除）。

### 验证局限性

- 未实际启动 Friday 进行端到端手动验证（需用户运行 Friday 后确认）
- 仅在 macOS 上验证，Windows 上未验证（fixplan 已确认方案兼容）

## 回归检查

### 改动范围确认

实际修改文件与 fixplan 一致：

| 文件 | fixplan 计划 | 实际改动 | 一致 |
|------|-------------|---------|------|
| `src/friday/knowledge/fts.py` | 新增 mtime 列 + 查询函数 | ✅ | ✅ |
| `src/friday/knowledge/adapter.py` | index_note 传递 mtime + 桥接函数 | ✅ | ✅ |
| `src/friday/knowledge/watcher.py` | reconcile + start_watcher 调用 | ✅ | ✅ |
| `tests/unit/test_fts.py` | 新增 mtime 测试 | ✅ | ✅ |
| `tests/unit/test_watcher.py` | 新增 reconcile 测试 | ✅ | ✅ |

### 未修改文件确认

- `src/friday/knowledge/store.py` — 未改动 ✅
- `src/friday/knowledge/vector.py` — 未改动 ✅
- `src/friday/cli/repl.py` — 未改动 ✅

### 公共接口影响

- `fts.insert()` 新增 `mtime` 参数（默认值 0.0），向后兼容 ✅
- `adapter.index_note()` 签名未变 ✅
- `start_watcher()` 签名未变 ✅

## 代码质量检查

| 检查项 | 结果 | 说明 |
|--------|------|------|
| 文件大小 ≤ 200 行 | ✅ | fts.py: 150, adapter.py: 155, watcher.py: 140 |
| 函数大小 ≤ 30 行 | ✅ | reconcile() 29 行，最长函数 |
| 类型注解 | ✅ | 所有新增函数均有类型注解 |
| 安全隐患 | ✅ | 无注入风险，SQL 使用参数化查询 |
| 冗余代码 | ✅ | 无临时代码残留 |
| 数据库迁移 | ✅ | ALTER TABLE 包裹在 try/except，兼容已有数据库 |

## 测试更新确认

| 测试文件 | 新增用例 | 运行结果 |
|----------|---------|---------|
| `tests/unit/test_fts.py` | `TestGetAllIndexMtimes`（3 个用例） | 9/9 passed |
| `tests/unit/test_watcher.py` | `TestReconcile`（4 个用例） | 12/12 passed |

## 结论

**修复有效**。代码改动严格遵循 fixplan，覆盖了新增/修改/删除三种离线变化场景，测试全部通过，无回归风险。

## 后续建议

- 用户启动 Friday 后，手动测试：关闭 → 添加/修改 notes 目录文件 → 启动 → 搜索验证
