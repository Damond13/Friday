# 缺陷报告: jieba 分词库 stdout 输出污染终端显示

**日期**: 2026-06-07 | **严重程度**: P1 | **状态**: 已验证

## 现象描述

交互模式下，当首次触发知识库 FTS 索引操作时，jieba 分词库向 stdout 输出加载日志，绕过 Rich Console 直接写入终端，导致：
1. 加载指示器（spinner）动画被破坏，显示乱序
2. LLM 回复内容被截断，与 jieba 日志混在一起
3. 后续交互中出现前一次回复的残留文字
4. 整体终端显示布局混乱

## 环境信息

- **操作系统**: macOS Darwin 24.5.0
- **Python 版本**: 3.13
- **Friday 版本**: a84fe79（012-cli-ux-polish 合并后）
- **相关依赖版本**: jieba>=0.42

## 复现步骤

1. 启动 Friday 交互模式：`uv run friday`
2. 发送任意触发知识库检索的消息（如"你能干什么"），确保 jieba 尚未被加载
3. 观察 LLM 回复和 spinner 动画区域

## 期望行为

jieba 加载过程不应向终端输出任何信息。spinner 动画和 LLM 回复应干净、无干扰地显示。

## 实际行为

终端输出中出现以下 jieba 日志，穿插在 spinner 和回复内容之间：
```
Loading model from cache /var/folders/ct/...
Loading model cost 0.258 seconds.
Prefix dict has been built successfully.
```
导致回复截断、spinner 位置错乱、后续交互内容残留。

## 影响范围

- **受影响功能**: 交互模式 REPL（所有涉及知识库 FTS 操作的交互）
- **影响用户**: 所有用户（jieba 首次加载时必现）
- **临时规避方法**: 在启动 Friday 前预先 import jieba（如 `python -c "import jieba"`）

## 附件

- 完整交互记录在会话上下文中
