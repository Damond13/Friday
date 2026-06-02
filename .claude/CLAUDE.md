# Friday — 个人 AI 助手

本地 CLI 工具，能记住知识、学会操作、自动执行。不是通用 AI，是"只属于你"的 AI 搭档。

## 核心差异化（三大支柱）

1. **深度个人化** — 只属于你的 AI，记住偏好、习惯、纠正
2. **自然学习** — 像教新同事一样，对话教学/录制操作/文档学习
3. **情境感知** — 知道你在哪个项目、在做什么、什么状态

## 技术栈

- Python 3.13 + Typer + Rich
- LLM: 智谱 API + DeepSeek API（可切换）
- 存储: SQLite + ChromaDB + 本地文件系统
- 记忆: Mem0（动态）+ 文件记忆（结构化）
- 开发: Claude Code + spec-kit SDD 工作流

## 项目文件结构

```
friday/
├── CLAUDE.md                    # 项目架构蓝图（本文件）
├── .claude/                     # Harness 配置
│   ├── commands/                # SDD 工作流命令（speckit.*）
│   ├── skills/                  # 领域知识技能（RAG/CLI/LLM）
│   └── agents/                  # 角色定义（开发者/审核者）
├── .specify/                    # Spec-Kit 配置和规格
│   └── memory/                  # SDD 过程记忆
├── .friday-memory/              # Mem0 动态记忆（ChromaDB）
├── specs/                       # 功能规格（SDD 产出）
├── src/friday/                  # 源代码
│   ├── cli/                     # 交互壳
│   ├── knowledge/               # 知识库
│   ├── executor/                # 执行器
│   ├── instruction/             # 指令学习
│   ├── memory/                  # 双层记忆系统
│   └── llm/                     # LLM 调用层
├── tests/
└── pyproject.toml
```

## 运行时数据目录

```
~/.friday/
├── config.yaml                  # 全局配置
├── profile.yaml                 # 用户画像
├── knowledge/notes/             # 用户笔记
├── knowledge/templates/         # 代码模板
├── instructions/                # 学到的指令（YAML）
├── sessions/                    # 会话历史
├── indexes/                     # 检索索引
└── logs/                        # 运行日志
```

## MVP 模块设计

### 交互壳 (cli/)
- `friday` 进入交互模式 / `friday "xxx"` 单次执行
- 斜杠命令 + 自然语言都支持
- 保存/恢复历史会话
- 助手风格，主动建议

### 知识库 (knowledge/)
- 对话式录入（"记一下 xxx"）
- 三层检索架构：
  1. **FTS5 文件索引** — 全文搜索，速度快，精确关键词匹配
  2. **ChromaDB 语义索引** — 向量检索，模糊/语义匹配，用 BGE-M3 或智谱 embedding
  3. **RAG 问答** — 检索 + LLM 综合，最智能但最慢
- 自动监控目录，文件变化自动更新索引
- 自动关联 + 手动标签

### 执行器 (executor/)
- Shell 直接执行（无容器隔离）
- 安全策略分级：
  - **安全指令**：直接执行（ls, cat, git status 等）
  - **新指令**：首次需用户确认，确认后加入白名单
  - **危险指令**：每次确认（rm -rf, 格式化等）
- 全盘文件访问权限
- 输出策略：短输出直接显示，长输出 AI 总结

### 指令学习 (instruction/)
- 对话式教学（"以后每次我说xxx，你就做xxx"）
- YAML 配置文件存储，可直接编辑
- 支持类型：
  - **单步指令**：一条命令 + 触发条件
  - **多步工作流**：有序步骤链
  - **条件分支**：if-else 逻辑
- 触发方式：对话关键词 / CLI 参数

### 双层记忆系统 (memory/)

**第一层：Mem0 动态记忆（自动）**
- 对话中自动提取值得记住的内容
- 用户偏好、习惯、纠正
- 语义检索（模糊匹配）
- 存储位置：项目下 `.friday-memory/`（ChromaDB）
- 按 project_id 分区

**第二层：结构化文件记忆（手动+Git管理）**
- `.specify/memory/constitution.md` — 开发原则
- `.specify/memory/decisions.md` — 架构决策记录（ADR）
- `.specify/memory/lessons-learned.md` — 踩坑记录
- `specs/*/review.md` — 审核记录

### LLM 调用层 (llm/)
- 多模型可切换（智谱 GLM / DeepSeek）
- System Prompt 组装：项目记忆 + 动态记忆 + 指令列表 + 知识上下文
- 工具调用：Shell 执行 / 文件读写 / 知识库检索

## 模块调用关系

```
用户输入 → cli/（交互壳）
         ↓
    llm/（LLM 调用层）
         ↓ 解析意图
    ┌────┼────┐
    ↓    ↓    ↓
knowledge/ executor/ instruction/
(知识检索) (执行命令) (指令匹配)
    ↓    ↓    ↓
    memory/（双层记忆）
    ↑         ↑
    └─ ChromaDB + SQLite ─┘
```

## 开发规范

- 使用 spec-kit SDD 工作流：constitution → specify → clarify → plan → tasks → implement → review
- Harness 审核分离：开发 Agent 写代码，审核 Agent 只读代码
- 所有代码通过 `uv run` 执行
- 测试用 pytest

### SDD 工作流完整流程

```
specify → clarify → plan → tasks → implement → review
                                                        ↓
                                                   APPROVED?
                                                  ↓ Yes    ↓ No
                                                  ↓    CHANGES REQUIRED
                                            合并到 main    修复 → 再 review
                                                  ↓
                                            推送远程
                                                  ↓
                                          删除功能分支
                                                  ↓
                                              完成
```

### 工作流规则

1. **文档生成前确认** — spec/plan/tasks/research 等文档生成前，必须展示草稿并等用户确认后再写入
2. **文档使用中文** — 所有 spec/plan/tasks/research 等文档内容使用中文（标题、描述、说明），代码变量名用英文
3. **审核上下文隔离** — 代码审核（/speckit.review）必须通过 Agent 工具启动独立子 Agent 执行，不在主会话中直接审核，避免开发偏见
4. **审核角色选择** — 使用 `.claude/agents/reviewer.md` 定义的审核角色，不用 superpowers:code-reviewer
5. **合并清理流程** — review APPROVED 后：合并到 main → 推送远程 → 删除功能分支，不留已完成的功能分支
