# 快速上手：CLI 交互壳

**功能分支**: `002-cli-shell` | **日期**: 2026-06-02

## 安装与运行

```bash
# 安装项目（开发模式）
uv sync

# 交互模式
uv run friday

# 单次执行
uv run friday "你好，Friday"
```

## 配置要求

运行前需配置 `~/.friday/config.yaml`：

```yaml
llm:
  provider: zhipu
  providers:
    zhipu:
      api_key: your-api-key-here
      model: glm-4-flash
```

## 交互模式示例

```text
$ friday

  Friday v0.1.0 — 你的专属 AI 搭档 💖
  输入 /help 查看可用命令

Friday> 今天天气怎么样

Friday: 我是一个本地助手，暂时无法获取实时天气数据。
       不过你可以教我如何查询天气！

Friday> /save
  ✓ 会话已保存

Friday> /exit
  再见！
```

## 关键文件

| 文件 | 职责 |
|------|------|
| `src/friday/cli/app.py` | 入口点，模式分发 |
| `src/friday/cli/repl.py` | REPL 循环，输入处理 |
| `src/friday/cli/slash.py` | 斜杠命令注册与分发 |
| `src/friday/cli/session.py` | 会话 JSON 存储 |
| `src/friday/cli/display.py` | Rich 输出格式化 |
