# Friday — 个人 AI 助手

## 项目定位
Friday 是一个本地 CLI 工具，能记住你教它的知识，学会你教它的操作，并自动替你执行。
核心差异化：深度个人化 + 自然学习 + 情境感知。

## 技术栈
- Python 3.11+
- Typer + Rich（CLI）
- 智谱 API + DeepSeek API（可切换）
- SQLite + ChromaDB（本地存储）
- Mem0（动态记忆）
- YAML（配置文件）

## 架构

```
用户 → CLI(Typer+Rich) → LLM调度层(智谱/DeepSeek)
                            ├── 知识库(FTS5+ChromaDB+RAG)
                            ├── 执行器(Shell+文件)
                            ├── 指令系统(YAML)
                            └── 记忆系统(Mem0+文件)
```

## 文件结构

```
src/friday/
├── cli/            # 交互壳（Typer+Rich）
│   ├── app.py      # CLI 入口
│   ├── chat.py     # 对话循环
│   └── commands.py # 斜杠命令
├── knowledge/      # 知识库
│   ├── storage.py  # CRUD（SQLite）
│   ├── indexer.py  # 索引（FTS5+ChromaDB）
│   ├── retriever.py# 检索（三层混合）
│   └── qa.py       # RAG 问答
├── executor/       # 执行器
│   ├── shell.py    # Shell 执行
│   ├── files.py    # 文件操作
│   └── safety.py   # 安全确认
├── instruction/    # 指令学习
│   ├── parser.py   # 解析对话中的指令
│   ├── runner.py   # 执行指令
│   └── store.py    # YAML 存取
├── memory/         # 记忆系统
│   ├── dynamic.py  # Mem0 动态记忆
│   └── context.py  # 上下文组装
├── llm/            # LLM 调用层
│   ├── adapter.py  # 统一适配（智谱/DeepSeek）
│   ├── prompts.py  # Prompt 模板
│   └── tools.py    # 工具定义
└── config.py       # 全局配置
```

## 编码规范
- 每个文件不超过 200 行
- 函数不超过 30 行
- 类型注解必须加
- 所有外部调用走 adapter 层，不直接依赖第三方 SDK
- 测试覆盖核心逻辑，CLI 层不写测试

## 数据存储
- 运行时数据：`~/.friday/`（config.yaml, knowledge/, instructions/, sessions/, indexes/, logs/）
- 项目内数据：`.friday-memory/`（Mem0 ChromaDB）
- 工程化数据：`.specify/`（spec-kit SDD 工作流）

## 开发工作流
使用 spec-kit 的 SDD 工作流：
1. `/speckit.constitution` — 项目原则
2. `/speckit.specify` — 功能规格
3. `/speckit.clarify` — 澄清遗漏
4. `/speckit.plan` — 实现计划
5. `/speckit.tasks` — 拆任务
6. `/speckit.implement` — 实现
7. `/speckit.review` — 审核（角色分离）

审核时使用 .claude/agents/ 下的角色定义，确保开发者和审核者分离。
