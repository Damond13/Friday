# 快速开始：知识库模块

**Feature**: 003-knowledge-base | **Date**: 2026-06-02

## 安装

```bash
uv add chromadb watchdog sentence-transformers jieba
```

## 首次使用

### 1. 录入知识

```bash
friday
Friday> 记一下 Python 装饰器就是函数包装器，可以在不修改原函数的情况下增强功能
```

或使用斜杠命令：

```bash
Friday> /note Flask 的蓝图用于组织大型应用的路由
```

### 2. 搜索知识

```bash
Friday> /search 装饰器
```

输出：
```
#1 Python 装饰器 (相关度: 0.95)
  Python 装饰器就是函数包装器，可以在不修改...
  来源: fts | ~/.friday/knowledge/notes/abc12345.md
```

### 3. 自然语言检索

在对话中自然提问：

```
Friday> 我之前说过什么关于装饰器的？
→ 系统自动使用语义检索 + RAG 回答
```

### 4. 文件自动索引

直接将文件放入知识目录，自动索引：

```bash
cp my-notes.md ~/.friday/knowledge/notes/
# 5 秒内自动进入索引
```

## 依赖说明

| 依赖 | 版本 | 用途 |
|------|------|------|
| chromadb | >=0.4 | 向量存储与检索 |
| watchdog | >=3.0 | 文件系统监控 |
| sentence-transformers | >=2.2 | 本地 embedding（bge-m3） |
| jieba | >=0.42 | 中文分词 |
