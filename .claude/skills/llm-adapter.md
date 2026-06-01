---
name: llm-adapter
description: LLM 调用层适配参考 — 多模型切换
---

# LLM 调用层

## 适配器模式
统一接口，支持智谱/DeepSeek 切换，上层代码不关心具体模型。

## 智谱 API
- 兼容 OpenAI 接口格式
- base_url: https://open.bigmodel.cn/api/paas/v4
- 模型: glm-4, glm-4-flash 等

## DeepSeek API
- 兼容 OpenAI 接口格式
- base_url: https://api.deepseek.com
- 模型: deepseek-chat, deepseek-coder 等

## 工具调用
- 使用 OpenAI 兼容的 function calling 格式
- 工具定义在 llm/tools.py
- 包含：execute_shell, read_file, write_file, search_knowledge, manage_instruction

## System Prompt 组装
动态组装：用户画像 + 指令列表 + 知识上下文 + Mem0 记忆
