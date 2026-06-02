# 接口契约：知识库公共 API

**Feature**: 003-knowledge-base | **Date**: 2026-06-02

## adapter.py — 上层模块调用入口

### add_note(title: str, content: str, tags: list[str] | None = None) -> Note

创建笔记并建立索引。

- **输入**: 标题、内容、可选标签
- **输出**: Note 对象
- **副作用**: 创建 Markdown 文件 + 更新 FTS5 和 ChromaDB 索引

### search(query: str, mode: str = "auto", limit: int = 5) -> list[SearchResult]

统一检索入口。

- **输入**: 查询文本、模式（"fts" / "vector" / "auto"）、返回数量
- **输出**: SearchResult 列表，按相关度降序
- **模式说明**:
  - "fts" — 仅 FTS5 关键词搜索
  - "vector" — 仅 ChromaDB 语义搜索
  - "auto" — 默认，FTS5 + ChromaDB 合并去重
- **降级**: ChromaDB 不可用时自动降级为仅 FTS5

### rag_query(query: str, limit: int = 5) -> str

RAG 问答：检索相关知识 + LLM 综合回答。

- **输入**: 用户问题
- **输出**: LLM 生成的回答字符串（基于检索到的知识）
- **流程**: search(auto) → 取前 N 条 → 拼 prompt → 调 LLM chat

### delete_note(note_id: str) -> bool

删除笔记及其索引。

- **输入**: 笔记 ID
- **输出**: 是否成功删除
- **副作用**: 删除文件 + 移除 FTS5 和 ChromaDB 索引

### list_notes(limit: int = 20, offset: int = 0) -> list[Note]

列出笔记。

- **输入**: 分页参数
- **输出**: Note 列表

### start_watcher() -> None

启动文件监控。

- **副作用**: watchdog Observer 后台线程开始监控 `~/.friday/knowledge/`

### stop_watcher() -> None

停止文件监控。

- **副作用**: 停止 Observer 线程

## embedding.py — 向量化接口

### embed_texts(texts: list[str]) -> list[list[float]]

将文本列表转为向量列表。

- **输入**: 文本列表
- **输出**: 对应的向量列表（1024 维）
- **实现**: 本地 bge-m3 模型推理

## CLI 斜杠命令契约

### /note <内容>

创建笔记。可选 `--tag` 参数添加标签。

### /search <查询>

搜索知识库。显示匹配结果列表（编号、标题、摘要、来源）。
