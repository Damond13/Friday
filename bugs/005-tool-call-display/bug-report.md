# 缺陷报告: 工具调用输出显示混乱

**日期**: 2026-06-07 | **严重程度**: P2 | **状态**: 已验证

## 现象描述

交互模式中，LLM 调用工具时（特别是 `shell_execute`），工具调用和结果的显示存在两个问题：

1. **长命令单行显示**：`show_tool_call` 将所有参数拼成一行，多行 Python 代码变成几百字符的单行，终端显示难以阅读
2. **结果截断乱码**：`show_tool_result` 将换行替换为空格后截断 200 字符，文件内容、代码等结构化输出变成不可读的一坨文字

## 环境信息

- **操作系统**: macOS Darwin 24.5.0
- **Python 版本**: 3.13
- **Friday 版本**: 6af5c1b（004-jieba-stdout-pollution 修复后）
- **相关代码**: `src/friday/cli/display.py:82-94`

## 复现步骤

1. 启动 Friday 交互模式：`uv run friday`
2. 发送需要工具调用的消息（如"添加到知识库"）
3. 观察 LLM 执行 `shell_execute` 时的工具调用和结果显示

## 期望行为

- 工具调用命令超过一定长度时应截断，只显示关键信息
- 工具结果应保留基本可读性，长结果截断但不破坏结构

## 实际行为

示例输出：
```
🔧 shell_execute command='python3 -c "\nfrom src.friday.knowledge.store import Note, generate_note_id, now_iso, create_note_file\nfrom datetime import datetime\n\nnote = Note(\n    id=generate_note_id(),\n    title='女朋友信息',\n...'
  ✓ --- id: e61e736c title: ：今天学会了 Friday 的所有功能模块，包括知识库、执行器、指令学习和记忆系统 tags: []  created_at: 2026-06-03T13:37:16 ---  ：今天学会了 Friday 的所有功能模块，包括知识库、执行器、指令学习和记忆系统
```

## 影响范围

- **受影响功能**: 交互模式中所有工具调用的显示
- **影响用户**: 所有使用交互模式的用户
- **临时规避方法**: 无

## 附件

- 完整交互记录在会话上下文中
