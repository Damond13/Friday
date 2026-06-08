# Research: 指令系统存储统一到知识库

**Date**: 2026-06-08 | **Feature**: 014-unify-instruction-storage

## 调研 1：开源助手如何管理用户自定义指令

### Khoj

- **方案**: Django + PostgreSQL，指令存储为 Agent 模型的 `personality` 字段（纯文本 system prompt）
- **启示**: Khoj 把"人格/指令"和"知识文档"分得很清 — 指令是 Agent 属性，知识是独立索引的内容
- **不采用原因**: 过于重量级（需 PostgreSQL + Django），Friday 是轻量 CLI

### Open Interpreter

- **方案**: YAML 配置文件 + Python profile，`custom_instructions` 是纯文本追加到 system message
- **启示**: 文件即配置，零基础设施，人可编辑。YAML 格式适合结构化指令
- **采用**: 保留 YAML 存储格式，符合 Friday 现有架构

## 调研 2：ChromaDB 类型区分最佳实践

- **ChromaDB 官方建议**: 同一 embedding 模型的数据用单个 collection + metadata 过滤，不要按类型拆 collection
- **metadata 过滤**: 支持 `$eq`, `$ne`, `$in`, `$contains` 等操作符，按 `type` 字段过滤即可区分
- **性能**: 在 <10K 记录规模下，metadata 过滤无性能问题

**决策**: 单 collection，增加 `type` metadata 字段。`"note"` 和 `"instruction"` 通过 `where` 过滤区分。

## 调研 3：结构化数据与自由文本共存

- **Pinecone 实验**: 结构化数据用"列头 + 值"格式向量化效果最好（V2 策略，7/7 准确率）
- **行业共识**: 混合方案为主流 — 结构化字段用关系型存储，语义搜索用向量索引，通过共享 ID 关联
- **核心原则**: 不要把结构化数据硬塞进纯文本文档

**决策**: 指令保持 YAML 存储（结构化字段自然表达），但内容向量化后进入 ChromaDB 索引。FTS 同理，内容（触发词 + 关键词 + 描述）进入全文索引。

## 调研 4：Friday 现有 FTS/ChromaDB 适配方案

### FTS5 改造

- `notes_fts` 表新增 `type TEXT DEFAULT 'note'` 列
- FTS 虚拟表和触发器同步增加 `type` 字段
- `search()` 增加 `entry_type` 参数，在 WHERE 子句中过滤
- 向后兼容：已有记录 `type` 为 NULL，视为 `"note"`

### ChromaDB 改造

- `upsert()` 的 metadata 增加 `"type": "note"` 或 `"type": "instruction"`
- `search()` 增加 `where={"type": entry_type}` 过滤
- 已有记录无 `type` 字段，不过滤时照常返回

## 决策汇总

| 决策 | 选择 | 理由 |
|------|------|------|
| 存储格式 | YAML 不变 | 结构化数据不适合 Markdown，人可编辑 |
| 索引层 | 共享 FTS + ChromaDB | 避免重复实现，语义检索解决匹配弱的问题 |
| 类型区分 | metadata `type` 字段 | ChromaDB 官方推荐，性能无忧 |
| 匹配方式 | 语义检索替代文本规则 | 解决"推到线上"匹配不上"部署"的问题 |
| 旧 matcher | 保留不删 | 向后兼容，但主流程不再调用 |
