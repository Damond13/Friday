# 技术调研：知识库模块

**Feature**: 003-knowledge-base | **Date**: 2026-06-02

## 决策 1：Embedding 模型选型

**决策**: 使用 `BAAI/bge-m3` 本地模型

**理由**:
- 支持 100+ 语言，中英跨语言检索能力强
- 技术笔记经常中英混合（"Python装饰器"、"RAG检索"），跨语言是刚需
- 本地运行，不调 API，不花 token，离线可用
- 560MB 模型体积可接受，个人工具磁盘不是瓶颈

**备选方案**:
- `bge-small-zh-v1.5`（90MB）— 中文最优但跨语言弱，将来需升级迁移
- `multilingual-e5-small`（470MB）— 多语言好但中文不如 bge 系列
- 智谱 API embedding — 需要网络，消耗 token，无法离线使用

## 决策 2：FTS5 中文分词

**决策**: 使用 jieba 分词后存入 FTS5

**理由**:
- SQLite FTS5 内置分词器对中文支持差，按字分词导致搜索质量低
- jieba 是成熟的中文分词库，准确率高
- 分词后以空格分隔存入 FTS5，查询时同样分词

**备选方案**:
- `simple` 扩展 — 支持拼音搜索，但增加编译依赖
- ICU tokenizer — 需要编译 ICU 库，复杂度高
- 纯按字分词 — 搜索质量差，不采用

## 决策 3：ChromaDB 存储配置

**决策**: 使用 `PersistentClient(path="~/.friday/knowledge/chroma")`

**理由**:
- 数据持久化到本地磁盘，重启不丢失
- 路径与知识目录统一管理（`~/.friday/knowledge/`）
- 自定义 EmbeddingFunction 集成 bge-m3

**备选方案**:
- `Client()` 内存模式 — 重启丢失，不可接受
- HttpClient — 需要启动服务端，过度工程

## 决策 4：文件监控方案

**决策**: 使用 watchdog Observer 后台线程

**理由**:
- Python 生态最成熟的文件监控库
- Observer.start() 非阻塞，适合 CLI 场景
- 支持递归监控子目录
- 事件驱动，文件变化时触发增量索引更新

**备选方案**:
- watchfiles（Rust 后端）— 更快但生态较新，watchdog 够用
- 轮询扫描 — 浪费资源，延迟高
- inotify 直接使用 — 平台不通用

## 决策 5：三层检索策略

**决策**: 按需递进，非三层全跑

**策略**:
- 简单搜索（`/search xxx`）→ 仅 FTS5，最快
- 语义搜索（自然语言查询）→ FTS5 + ChromaDB 合并去重
- RAG 问答（综合问题）→ 前两层结果 + LLM 综合回答

**理由**: 避免每次都跑三层造成不必要的延迟和资源消耗
