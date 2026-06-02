# 实现计划：CLI 交互壳

**分支**: `002-cli-shell` | **日期**: 2026-06-02 | **规格**: [spec.md](spec.md)

**输入**: 功能规格 `/specs/002-cli-shell/spec.md`

## 概要

实现 Friday 的 CLI 用户入口，支持交互模式（REPL）和单次执行模式，集成 LLM 适配层进行流式对话，支持斜杠命令和会话持久化。使用 Typer 定义 CLI 入口，Rich 处理终端输出，prompt_toolkit 提供交互式输入。

## 技术上下文

**语言/版本**: Python 3.13

**主要依赖**: Typer（CLI 框架）、Rich（终端美化）、prompt_toolkit（交互输入）

**存储**: 本地文件系统（`~/.friday/sessions/`，JSON 格式）

**测试**: pytest + unittest.mock（单元测试核心逻辑，CLI 交互层不写测试）

**目标平台**: macOS / Linux 终端

**项目类型**: CLI 工具

**性能目标**: 交互模式启动 <1s，流式输出首 token <2s，斜杠命令 <0.5s

**约束**: 每文件 ≤200 行，每函数 ≤30 行，所有类型注解

**规模**: 单用户本地工具

## 宪法检查

*门控：必须在 Phase 0 研究前通过。Phase 1 设计后重新检查。*

| 原则 | 状态 | 说明 |
|------|------|------|
| I. 个人化优先 | ✅ | CLI 是个人专属入口，交互风格为助手型 |
| II. 渐进式学习 | ✅ | 斜杠命令作为结构化操作入口，自然语言为主 |
| III. 本地优先 | ✅ | 会话存储在本地文件系统 |
| IV. 安全可控 | ✅ | CLI 层不涉及命令执行，由 executor 模块负责 |
| V. 简洁实用 | ✅ | CLI 工具，Rich 美化但不花哨，短输出直接显示 |
| 技术栈约束 | ✅ | Typer + Rich，符合要求 |
| 编码规范 | ✅ | 文件/函数大小限制，类型注解，adapter 层调用 |
| 模块边界 | ✅ | cli/ 只管交互（输入/输出/会话管理），不包含业务逻辑 |
| 开发流程 | ✅ | 使用 SDD 工作流，审核分离 |

**无违规项。**

## 项目结构

### 文档（本功能）

```text
specs/002-cli-shell/
├── plan.md              # 本文件
├── research.md          # Phase 0 输出
├── data-model.md        # Phase 1 输出
├── quickstart.md        # Phase 1 输出
├── contracts/           # Phase 1 输出
│   └── cli-commands.md  # 斜杠命令契约
└── tasks.md             # Phase 2 输出（/speckit.tasks）
```

### 源代码

```text
src/friday/cli/
├── __init__.py          # 模块导出
├── app.py               # Typer 入口 + main()，两种模式分发
├── repl.py              # 交互模式 REPL 循环
├── slash.py             # 斜杠命令注册与分发
├── session.py           # 会话加载/保存（JSON 文件）
├── display.py           # Rich 输出格式化（欢迎信息、错误、状态）

tests/unit/
├── test_session.py      # 会话存储单元测试
└── test_slash.py        # 斜杠命令分发单元测试
```

**结构决策**: CLI 模块按职责拆分为 5 个文件，每个文件不超过 200 行。app.py 作为入口，repl.py 处理 REPL 循环，slash.py 管理命令分发，session.py 处理会话持久化，display.py 负责输出格式化。
