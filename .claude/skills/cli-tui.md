---
name: cli-tui
description: CLI/TUI 实现参考 — Typer + Rich
---

# CLI 交互壳

## 技术选择
- Typer：命令行框架，自动生成帮助信息
- Rich：终端富文本渲染（表格、进度条、Markdown 渲染）

## 交互模式
- `friday` → 进入交互式 REPL（多轮对话）
- `friday "帮我xxx"` → 单次执行，输出结果后退出
- 斜杠命令：`/help` `/note` `/history` `/clear` 等

## 对话展示
- LLM 回答用 Rich Markdown 渲染
- Shell 执行结果：短输出直接显示，长输出 AI 总结
- 工具调用过程实时展示（如"正在搜索知识库..."）

## 会话管理
- 对话历史存 ~/.friday/sessions/
- 支持恢复上次会话
