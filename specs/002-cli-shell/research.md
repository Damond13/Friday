# 研究报告：CLI 交互壳

**功能分支**: `002-cli-shell` | **日期**: 2026-06-02

## 技术决策

### 1. 交互输入方案：prompt_toolkit

**决策**: 使用 prompt_toolkit 的 PromptSession 构建 REPL 循环

**理由**:
- 内置历史记录支持（FileHistory），会话间持久化
- 优雅处理 KeyboardInterrupt 和 EOFError
- 支持自定义提示符样式
- 比 readline 更跨平台、更灵活

**备选方案**:
- Python 内置 `input()` — 功能简单，无历史记录，Ctrl+C 处理粗糙
- click.prompt — Typer/Click 自带，但不适合多轮对话

### 2. 流式输出方案：Rich Console

**决策**: 使用 Rich Console 直接 print 流式 token，而非 Live 组件

**理由**:
- `chat_stream()` 返回 `Iterator[str]`，逐 token 输出，直接 print 最自然
- Live 组件适合动态更新同一区域（如进度条），不适合逐字追加
- Console.print 支持 Markdown 渲染，可对完整回复做后渲染

**备选方案**:
- Rich Live — 适合原地更新，不适合流式追加
- 纯 print — 无颜色、无 Markdown 渲染

### 3. CLI 入口方案：Typer

**决策**: 使用 Typer 定义入口，可选参数 `message: str` 区分两种模式

**理由**:
- `friday` → message=None → 交互模式
- `friday "问题"` → message 有值 → 单次执行
- pyproject.toml 已定义入口 `friday.cli.app:main`

### 4. 会话存储格式：JSON 文件

**决策**: 每个会话一个 JSON 文件，存储在 `~/.friday/sessions/`

**理由**:
- 结构简单，人类可读，易于调试
- 单用户本地工具，无需数据库
- 文件名用时间戳确保唯一性

**备选方案**:
- SQLite — 过度设计，单用户场景不需要
- YAML — 不适合存储长文本内容（转义问题）

### 5. Ctrl+C 处理策略

**决策**: REPL 循环中捕获 KeyboardInterrupt，中断流式输出回到提示符；连续两次退出

**理由**:
- 符合用户对 CLI REPL 的直觉预期
- 第一次中断当前操作，第二次退出程序
- 参照 IPython、Python REPL 等常见模式
