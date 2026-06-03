# Friday 项目状态报告

**生成日期**：2026-06-03
**项目阶段**：MVP 全部 6 模块开发完成

---

## 一、项目概况

**Friday** 是一个本地 CLI 个人 AI 助手，能记住知识、学会操作、自动执行命令。
基于 Python 3.13 开发，使用 spec-kit SDD 工作流驱动。

| 指标 | 数值 |
|------|------|
| 源码文件 | 34 个 |
| 源码总行数 | 3,054 行 |
| 测试文件 | 18 个 |
| 测试用例 | 156 个（154 通过，2 跳过） |
| 模块数 | 6 个 |
| Git 提交 | 13 次 |
| 依赖包 | 10 个核心 + 3 个开发 |

---

## 二、架构报告

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    CLI 交互壳 (cli/)                      │
│   app.py → repl.py → slash.py → session.py → display.py │
└──────────────────────┬──────────────────────────────────┘
                       │ 用户输入/输出
┌──────────────────────▼──────────────────────────────────┐
│                  LLM 调度层 (llm/)                        │
│   adapter.py → prompts.py → tools.py → types.py          │
└──┬──────────┬──────────┬──────────┬──────────────────────┘
   │          │          │          │
   ▼          ▼          ▼          ▼
┌──────┐ ┌────────┐ ┌──────────┐ ┌───────────┐
│知识库│ │ 执行器  │ │指令学习   │ │ 双层记忆   │
│knowledge/│executor/│instruction/│ memory/    │
│FTS5+ChromaDB│Shell+安全│YAML+匹配│Mem0+文件│
└──────┘ └────────┘ └──────────┘ └───────────┘
```

### 2.2 模块间依赖关系

```
cli/ ──→ llm/ ──→ config.py
              ├──→ knowledge/ (RAG 检索)
              ├──→ executor/ (工具执行)
              ├──→ instruction/ (指令匹配)
              └──→ memory/ (记忆存取)
```

模块间通过 **adapter.py** 统一接口通信，无循环依赖。

### 2.3 每个模块的内部结构

| 模块 | 文件数 | 总行数 | 内部层次 |
|------|--------|--------|----------|
| cli/ | 6 | 511 | app → repl → slash → session → display |
| llm/ | 5 | 390 | adapter → prompts → tools → types |
| knowledge/ | 7 | 693 | adapter → fts + vector + store + watcher → embedding |
| executor/ | 6 | 612 | adapter → runner → safety → history → output → errors |
| instruction/ | 5 | 402 | adapter → matcher → store → models |
| memory/ | 4 | 446 | adapter → dynamic + files |

### 2.4 设计模式

- **Adapter 模式**：每个模块对外只暴露 `adapter.py`，内部实现隔离
- **存储层分离**：knowledge(store)、instruction(store)、memory(files+dynamic) 各自独立存储
- **降级容错**：Mem0 初始化失败时返回空结果，不阻断主流程
- **安全分级**：executor 的命令按信任等级分三级处理

---

## 三、功能报告

### 3.1 CLI 交互壳 (cli/ — 511 行)

| 功能 | 文件 | 说明 |
|------|------|------|
| 入口命令 | app.py | `friday` 交互模式 / `friday "xxx"` 单次执行 |
| REPL 循环 | repl.py | 多行输入、上下文、自动补全 |
| 斜杠命令 | slash.py | `/help` `/config` `/session` `/knowledge` `/memory` 等 |
| 会话管理 | session.py | 保存/加载/列表历史会话 |
| UI 渲染 | display.py | Rich 格式化输出、错误展示、配置引导 |

**公共 API**：`app`, `main`, `Session`, `Message`, `CommandResult`, `repl_loop`

### 3.2 LLM 调度层 (llm/ — 390 行)

| 功能 | 文件 | 说明 |
|------|------|------|
| 统一接口 | adapter.py | 智谱 GLM / DeepSeek 双模型切换 |
| Prompt 组装 | prompts.py | System Prompt + 用户记忆 + 知识上下文 |
| 工具调用 | tools.py | shell 执行、文件读写、知识库检索 |
| 类型定义 | types.py | LLMResponse, ToolCall, TokenUsage |

**公共 API**：`chat()`, `chat_stream()`, `get_client()`, `switch_provider()`

### 3.3 知识库 (knowledge/ — 693 行)

| 功能 | 文件 | 说明 |
|------|------|------|
| 统一接口 | adapter.py | 三层检索：FTS5 → ChromaDB → RAG |
| 全文索引 | fts.py | SQLite FTS5 中文分词 + jieba |
| 向量索引 | vector.py | ChromaDB + sentence-transformers 嵌入 |
| 笔记存储 | store.py | 文件系统持久化 + 元数据管理 |
| 文件监控 | watcher.py | watchdog 自动检测文件变化并重建索引 |
| 嵌入工具 | embedding.py | 文本向量化 |

**公共 API**：`add_note()`, `delete_note()`, `search()`, `rag_query()`

### 3.4 执行器 (executor/ — 612 行)

| 功能 | 文件 | 说明 |
|------|------|------|
| 统一接口 | adapter.py | 执行流水线：安全检查 → 运行 → 输出处理 |
| Shell 运行 | runner.py | 子进程执行、超时控制、流式输出 |
| 安全策略 | safety.py | 三级分类：安全(直接) / 新指令(首次确认) / 危险(每次确认) |
| 历史记录 | history.py | 执行日志持久化、查询、统计 |
| 输出策略 | output.py | 短输出直显，长输出 AI 总结 |
| 异常定义 | errors.py | CommandDeniedError, CommandNotFoundError |

**公共 API**：`execute()`, `execute_stream()`

### 3.5 指令学习 (instruction/ — 402 行)

| 功能 | 文件 | 说明 |
|------|------|------|
| 统一接口 | adapter.py | teach(), match(), remove(), reload() |
| 模式匹配 | matcher.py | 精确匹配 → 子串匹配 → Jaccard 相似度 |
| 数据模型 | models.py | Instruction, Action, InstructionType, MatchResult |
| YAML 存储 | store.py | 每条指令一个 YAML 文件，支持 slug 化文件名 |

**公共 API**：`teach()`, `match()`, `list_instructions()`, `remove()`, `reload()`

### 3.6 双层记忆 (memory/ — 446 行)

| 功能 | 文件 | 说明 |
|------|------|------|
| 统一接口 | adapter.py | 合并动态 + 文件两层检索结果 |
| 动态记忆 | dynamic.py | Mem0 + ChromaDB，语义检索对话记忆 |
| 文件记忆 | files.py | decisions.md / lessons-learned.md / constitution.md |

**公共 API**：`add_memory()`, `search_memories()`, `add_decision()`, `add_lesson()`, `get_constitution()`

---

## 四、功能进度报告

### 4.1 模块完成度

| 模块 | 开发状态 | 测试状态 | 审核状态 | 合并状态 |
|------|----------|----------|----------|----------|
| llm/ | ✅ 完成 | ✅ 21 测试 | ✅ 通过 | ✅ 已合并 |
| cli/ | ✅ 完成 | ✅ 47 测试 | ✅ 通过 | ✅ 已合并 |
| knowledge/ | ✅ 完成 | ✅ 34 测试 | ✅ 通过 | ✅ 已合并 |
| executor/ | ✅ 完成 | ✅ 27 测试 | ✅ 通过 | ✅ 已合并 |
| instruction/ | ✅ 完成 | ✅ 36 测试 | ✅ 通过 | ✅ 已合并 |
| memory/ | ✅ 完成 | ✅ 17 测试 | ✅ 通过 | ✅ 已合并 |

### 4.2 MVP 功能清单对照

| MVP 功能 | 实现状态 | 对应模块 |
|----------|----------|----------|
| `friday` 交互模式 / 单次执行 | ✅ | cli/app.py |
| 斜杠命令系统 | ✅ | cli/slash.py |
| 会话保存/恢复 | ✅ | cli/session.py |
| 多模型切换（智谱/DeepSeek） | ✅ | llm/adapter.py |
| System Prompt 组装 | ✅ | llm/prompts.py |
| 工具调用（Shell/文件/检索） | ✅ | llm/tools.py |
| FTS5 全文检索 | ✅ | knowledge/fts.py |
| ChromaDB 语义检索 | ✅ | knowledge/vector.py |
| RAG 问答 | ✅ | knowledge/adapter.py |
| 文件变化自动索引 | ✅ | knowledge/watcher.py |
| Shell 命令执行 | ✅ | executor/runner.py |
| 安全策略分级 | ✅ | executor/safety.py |
| 执行历史记录 | ✅ | executor/history.py |
| 对话式指令教学 | ✅ | instruction/adapter.py |
| 触发模式匹配 | ✅ | instruction/matcher.py |
| YAML 指令存储 | ✅ | instruction/store.py |
| Mem0 动态记忆 | ✅ | memory/dynamic.py |
| 结构化文件记忆 | ✅ | memory/files.py |
| 统一双层检索 | ✅ | memory/adapter.py |

### 4.3 尚未完成 / 待补充

| 项目 | 状态 | 说明 |
|------|------|------|
| 跨模块集成测试 | ⬜ 未开始 | 模块间端到端调用链路未测试 |
| Mem0 实际集成验证 | ⬜ 需 LLM 配置 | 2 个测试因需 API Key 跳过 |
| CLI 入口端到端测试 | ⬜ 未开始 | 需真实 LLM 环境验证 |
| LLM 工具调用集成 | ⬜ 未开始 | 工具定义存在，但与 executor/knowledge 的联调未做 |
| 用户画像 (profile.yaml) | ⬜ 未实现 | config 中预留但未开发 |
| 日志系统 | ⬜ 未实现 | logs/ 目录预留但未接入 |

### 4.4 技术债务

- 无跨模块集成测试，模块间交互的正确性未验证
- LLM 工具调用（tools.py 中定义的 schema）与 executor/knowledge 的实际对接未完成
- 错误处理在各模块边界不够一致（部分直接抛异常，部分降级返回空）

---

## 五、依赖清单

**核心依赖**（10 个）：

| 包 | 用途 |
|----|------|
| typer | CLI 框架 |
| rich | 终端 UI 渲染 |
| openai | LLM SDK（智谱/DeepSeek 均兼容） |
| chromadb | 向量数据库 |
| mem0ai | 动态记忆管理 |
| pyyaml | YAML 配置读写 |
| jieba | 中文分词 |
| sentence-transformers | 文本嵌入模型 |
| prompt-toolkit | REPL 交互增强 |
| watchdog | 文件系统监控 |

**开发依赖**（3 个）：pytest, pytest-asyncio, ruff

---

## 六、Git 提交历史

```
d6445bf feat: 实现双层记忆系统
9bc748a feat: 实现指令学习模块
dce696d feat: 实现执行器模块
5dbf706 feat: 实现知识库模块
d53a0f5 feat: 实现 CLI 交互壳模块
206afd2 docs: 添加 README.md
e420227 docs: 合并两个 CLAUDE.md 为一个
f486b20 docs: 将工作流规则写入 .claude/CLAUDE.md
26eef53 merge: 合并远程初始提交到本地 main
067a686 chore: initialize Friday project scaffold
c3bc656 feat: 实现 LLM 统一适配层
6ab3df0 chore: 清理 .github/ 下旧的 speckit copilot 配置文件
40fe15e chore: initialize Friday project scaffold
7b1c479 Initial commit
```

---

## 七、下一步建议

1. **集成联调**：将 LLM 工具调用与 executor/knowledge/instruction/memory 打通，实现端到端对话流程
2. **集成测试**：编写跨模块测试，验证完整调用链路
3. **日志系统**：接入统一的 Python logging，输出到 `~/.friday/logs/`
4. **用户画像**：开发 profile.yaml 的读写和 LLM 注入
5. **打包发布**：配置 `pyproject.toml` 的完整元数据，支持 `pip install` 安装
