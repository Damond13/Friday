# 数据模型：执行器模块

**Branch**: `004-executor` | **Date**: 2026-06-02

## 实体定义

### ExecutionRecord（执行记录）

每次命令执行的完整记录。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 自增主键 |
| command | TEXT | 完整命令文本 |
| cwd | TEXT | 执行时的工作目录 |
| exit_code | INTEGER | 退出码（0=成功，None=超时/取消） |
| stdout | TEXT | 标准输出（截断至 4KB） |
| stderr | TEXT | 标准错误（截断至 4KB） |
| started_at | TEXT | 开始时间（ISO8601） |
| finished_at | TEXT | 结束时间（ISO8601） |
| duration_ms | INTEGER | 执行耗时（毫秒） |
| safety_level | TEXT | 安全等级：safe / confirm / dangerous |
| approved | BOOLEAN | 是否经过用户确认 |

**索引**：
- `idx_exec_started_at` ON `started_at`（按时间查询和清理）
- `idx_exec_command` ON `command`（按命令名统计）

**清理策略**：`DELETE FROM execution_log WHERE started_at < datetime('now', '-90 days')`

### SafetyRule（安全策略规则）

命令的安全分类规则，存储在代码常量中（MVP 不持久化到 DB）。

| 字段 | 类型 | 说明 |
|------|------|------|
| pattern | str | 匹配模式（命令名或正则） |
| level | enum | safe / confirm / dangerous |
| description | str | 规则说明 |

**默认规则**：

- **safe 白名单**：ls, pwd, cat, head, tail, echo, wc, find, grep, which, date, whoami, uname, git, diff, tree, file, stat
- **dangerous 黑名单**（正则匹配）：`rm\s+(-rf|-fr)`, `rmdir`, `sudo\s+`, `chmod\s+`, `chown\s+`, `mkfs`, `dd\s+if=`, `> /dev/sd`, `shutdown`, `reboot`, `systemctl\s+(stop|disable|mask)`, `pip\s+install.*--force`, `npm\s+publish`

### TrustedCommand（用户信任命令）

用户标记为信任的非危险命令，存储在 SQLite 中。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 自增主键 |
| command_pattern | TEXT | 信任的命令模式（精确匹配命令名） |
| trusted_at | TEXT | 信任时间（ISO8601） |

**唯一约束**：`UNIQUE(command_pattern)`

## 实体关系

```
SafetyRule（内存常量）
    ↓ 分类结果
ExecutionRecord.safety_level

TrustedCommand（SQLite）
    ↓ 提升安全等级
SafetyRule 评估时可提升 confirm → safe
```

## SQLite 表 DDL

```sql
CREATE TABLE IF NOT EXISTS execution_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command TEXT NOT NULL,
    cwd TEXT NOT NULL,
    exit_code INTEGER,
    stdout TEXT DEFAULT '',
    stderr TEXT DEFAULT '',
    started_at TEXT NOT NULL,
    finished_at TEXT,
    duration_ms INTEGER,
    safety_level TEXT NOT NULL CHECK(safety_level IN ('safe', 'confirm', 'dangerous')),
    approved INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_exec_started_at ON execution_log(started_at);
CREATE INDEX IF NOT EXISTS idx_exec_command ON execution_log(command);

CREATE TABLE IF NOT EXISTS trusted_commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command_pattern TEXT NOT NULL UNIQUE,
    trusted_at TEXT NOT NULL
);
```

## 数据存储位置

- SQLite 数据库：`~/.friday/executor.db`
- WAL 模式启用
