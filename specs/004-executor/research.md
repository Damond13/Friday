# 研究报告：执行器模块

**Branch**: `004-executor` | **Date**: 2026-06-02

## 1. Python asyncio 子进程最佳实践

**决策**：使用 `asyncio.create_subprocess_shell` 执行命令，配合 `asyncio.wait_for` 超时控制，`process.terminate()` → `process.kill()` 优雅退出。

**理由**：执行器需要支持 Shell 特性（管道 `|`、重定向 `>`、通配符 `*`），必须用 `shell=True` 模式。`asyncio.wait_for` 提供精确超时。信号处理用 `loop.add_signal_handler` 转发 SIGINT 给子进程。

**备选方案**：
- `subprocess.run`（同步，无法流式输出和取消）
- `create_subprocess_exec`（避免 shell 注入，但不支持管道/通配符）
- `sh` 库（API 更 Pythonic 但不支持 async）

## 2. Shell 命令安全分级策略

**决策**：三级分类 + 正则规则引擎。安全（白名单匹配直接执行）→ 需确认（首次确认后记忆）→ 危险（黑名单匹配，每次确认）。deny 优先级最高。

**理由**：Cursor 的纯黑名单方案被证明有根本缺陷（The Denylist Delusion）。Claude Code 采用 `deny → ask → allow` 优先级链。我们结合两者：基础命令白名单标记为安全，危险模式标记为危险，其余归为需确认。白名单用命令名精确匹配，黑名单用正则模式匹配命令+参数。

**备选方案**：
- 纯黑名单（不安全，易绕过）
- 纯白名单（过于严格）
- LLM 判断安全性（不可靠，有 prompt injection 风险）
- 容器沙箱隔离（安全但启动慢、依赖重）

## 3. SQLite 命令执行历史表设计

**决策**：单表 `execution_log`，WAL 模式，stdout/stderr 截断存储（前 4KB），定期清理保留 90 天。索引放在 `started_at` 和 `command` 上。

**理由**：单表满足 CLI 工具需求，无需复杂审计。`started_at` 索引支持按时间查询和清理。stdout/stderr 截断避免大输出撑大数据库。WAL 模式支持并发读写。

**备选方案**：
- 父子表分离（更规范但查询复杂）
- JSON 列存储（灵活但无法高效索引）
- 纯文件日志（大输出场景更好但架构复杂）
