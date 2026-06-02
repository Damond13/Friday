<!--
Sync Impact Report
==================
Version: 1.0 → 1.1.0 (MINOR bump — added Governance section + Coding Standards)
Modified principles: none (all 5 principles preserved as-is)
Added sections:
  - 编码规范 (Coding Standards)
  - Governance (amendment procedure, versioning, compliance)
Removed sections: none
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ (Constitution Check aligns with principles)
  - .specify/templates/spec-template.md ✅ (no conflicts)
  - .specify/templates/tasks-template.md ✅ (task categorization compatible)
Follow-up TODOs: none
-->

# Friday Constitution

## 核心原则

### I. 个人化优先
Friday 是用户专属的 AI 助手，所有设计决策以"深度个人化"为第一优先级。记忆用户偏好、习惯、纠正是核心能力。

### II. 渐进式学习
像教新同事一样，从简单到复杂。用户不需要懂技术细节就能教会 Friday 新技能。对话教学、录制操作、文档学习三种方式并行。

### III. 本地优先
所有数据存储在本地（SQLite + ChromaDB + 文件系统），用户拥有完全控制权。不依赖云服务。

### IV. 安全可控
执行器分级安全策略：安全指令自动执行，新指令首次确认，危险指令每次确认。用户始终有最终决定权。

### V. 简洁实用
CLI 工具，不追求花哨 UI，追求效率和实用性。短输出直接显示，长输出 AI 总结。

## 技术栈约束

- Python 3.13 + Typer（CLI 框架）
- SQLite（结构化存储）+ ChromaDB（向量检索）
- 智谱 API 默认 LLM，DeepSeek 作为备选，通过 adapter 模式切换
- Mem0 管理动态记忆
- YAML 存储指令和配置（人可读，易编辑）

## 编码规范

- 每个文件不超过 200 行，函数不超过 30 行
- 类型注解必须加
- 所有外部调用走 adapter 层，不直接依赖第三方 SDK
- 测试覆盖核心逻辑，CLI 层不写测试
- 代码通过 `uv run` 执行，测试用 pytest

## 模块边界

- **cli/** — 只管交互（输入/输出/会话管理），不包含业务逻辑
- **knowledge/** — 只管知识的存取和检索（FTS5 + ChromaDB + RAG），不关心展示
- **executor/** — 只管执行命令和安全管理，不关心为什么执行
- **instruction/** — 只管指令的存储和匹配，不执行
- **memory/** — 只管记忆的存取，是其他模块的底层支撑
- **llm/** — 只管 LLM 调用和 prompt 组装，是决策中枢

## 开发流程

- 使用 spec-kit SDD 工作流
- Harness 审核分离：开发 Agent 写代码，审核 Agent 只读
- 所有功能 MUST 通过 constitution 检查后才能进入 Phase 0

## Governance

宪法是 Friday 项目的最高开发准则，所有其他实践文件以本文件为准。

- **修订流程**：任何原则变更 MUST 附带变更原因、影响范围说明和迁移计划
- **版本策略**：语义化版本（MAJOR.MINOR.PATCH）
  - MAJOR：原则删除或根本性重定义
  - MINOR：新增原则/章节或实质性扩展
  - PATCH：措辞澄清、排版修复
- **合规检查**：每个功能的 plan.md MUST 包含 Constitution Check 章节
- **运行时指导**：开发过程中遵循 `.claude/CLAUDE.md` 和 `.specify/memory/` 下的决策记录

**Version**: 1.1.0 | **Ratified**: 2026-06-01 | **Last Amended**: 2026-06-01
