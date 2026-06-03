# Friday 用户使用手册

> Friday — 你的专属 AI 搭档，能记住你教它的知识，学会你教它的操作，并自动替你执行。

---

## 1. 快速开始

### 1.1 安装

```bash
# 克隆项目
git clone <repo-url> friday && cd friday

# 安装依赖（使用 uv）
uv sync
```

### 1.2 配置 LLM

首次使用需配置 AI 模型的 API Key。编辑 `~/.friday/config.yaml`：

```yaml
llm:
  provider: zhipu
  providers:
    zhipu:
      api_key: 你的智谱-API-Key
      model: glm-4.7
      max_tokens: 4096
```

**支持的 Provider**:

| Provider | Base URL（自动填充） | 模型示例 |
|----------|---------------------|----------|
| zhipu | `https://open.bigmodel.cn/api/paas/v4/` | glm-4.7, glm-4-flash |
| deepseek | `https://api.deepseek.com` | deepseek-chat |

如需自定义 base_url，可在 provider 配置中添加 `base_url` 字段。

### 1.3 运行

```bash
# 交互模式（推荐）
uv run friday

# 单次提问模式
uv run friday "你好，介绍一下你自己"
```

---

## 2. 交互模式

启动交互模式后，你会看到欢迎界面和 `Friday>` 提示符：

```
╭───────────────────────────────────╮
│ Friday v0.1.0 — 你的专属 AI 搭档  │
╰───────────────────────────────────╯

输入 /help 查看可用命令

Friday>
```

### 2.1 基本对话

直接输入文字即可与 Friday 对话，支持多轮上下文：

```
Friday> 你好
────────────────────
Friday: 你好！有什么可以帮你的？

Friday> 帮我写一个 Python 的 hello world
────────────────────
Friday: 没问题！这是脚本：

```python
print("Hello, World!")
```

保存为 `hello.py` 后运行 `python hello.py` 即可。
```

### 2.2 快捷笔记

对话中输入"记一下 xxx"可快速录入知识库：

```
Friday> 记一下：项目的 API 基础地址是 https://api.example.com/v2
✓ 已记录笔记 (id: a1b2c3d4)
```

支持的前缀：`记一下`、`记录一下`、`记一下：`、`记一下:`

### 2.3 退出

- 输入 `/exit` 或 `/quit` 退出
- 连续按两次 `Ctrl+C` 退出
- 按 `Ctrl+D` 退出

---

## 3. 斜杠命令

在交互模式中，输入 `/命令名` 执行特定操作：

### 3.1 命令列表

| 命令 | 格式 | 说明 |
|------|------|------|
| `/help` | `/help` | 显示所有可用命令 |
| `/note` | `/note <内容>` | 记录知识笔记到知识库 |
| `/search` | `/search <关键词>` | 搜索知识库中的笔记 |
| `/save` | `/save` | 保存当前会话 |
| `/history` | `/history` | 列出历史会话 |
| `/load` | `/load <编号>` | 恢复历史会话 |
| `/exit` | `/exit` | 退出交互模式 |
| `/quit` | `/quit` | 退出交互模式 |

### 3.2 使用示例

#### 记录笔记

```
Friday> /note Git 常用命令：git status, git add, git commit -m "message"
✓ 已记录笔记 (id: e5f6g7h8)
```

#### 搜索知识库

```
Friday> /search Git
  #1 Git 常用命令 [fts]
      git status, git add, git commit -m "message"
      ~/.friday/knowledge/notes/e5f6g7h8.md
```

#### 保存与恢复会话

```
Friday> /save
✓ 会话已保存到 /Users/you/.friday/sessions/a1b2c3d4.json

Friday> /history
┌──────┬────────────────────┬────────────────────┐
│ 编号 │ 时间               │ 摘要               │
├──────┼────────────────────┼────────────────────┤
│ 1    │ 2026-06-03T13:00:00│ 你好               │
└──────┴────────────────────┴────────────────────┘

Friday> /load 1
✓ 已加载会话 (3 条消息)
```

---

## 4. 知识库

知识库用于存储和检索你的个人知识。每条笔记以 Markdown 文件存储在 `~/.friday/knowledge/notes/` 下。

### 4.1 添加知识

三种方式：

```bash
# 1. 斜杠命令
Friday> /note Python 3.13 引入了实验性 JIT 编译器

# 2. 快捷语法
Friday> 记一下：部署环境是 Ubuntu 22.04，Python 3.13

# 3. 直接编辑 Markdown 文件
# 创建 ~/.friday/knowledge/notes/xxx.md
```

笔记文件格式（自动生成）：

```markdown
---
id: a1b2c3d4
title: Python 3.13 引入了实验性 JIT 编译器
tags: []
created_at: 2026-06-03T13:00:00
---

Python 3.13 引入了实验性 JIT 编译器
```

### 4.2 搜索知识

```
Friday> /search Python
```

搜索支持两种模式：
- **FTS5 全文搜索**（默认可用）：基于关键词匹配，速度快，支持中文分词
- **向量语义搜索**（需首次下载模型）：基于语义相似度，能匹配含义相近的内容

### 4.3 知识文件管理

笔记存储在 `~/.friday/knowledge/notes/`，可直接用文本编辑器管理：

```bash
# 查看所有笔记
ls ~/.friday/knowledge/notes/

# 编辑某条笔记
vim ~/.friday/knowledge/notes/a1b2c3d4.md

# 删除笔记（同时清理索引）
rm ~/.friday/knowledge/notes/a1b2c3d4.md
```

文件修改后，文件监控器会自动更新索引。

---

## 5. 指令学习

教 Friday 记住你的操作习惯。例如："以后每次我说'看状态'，你就执行 git status"。

### 5.1 通过 API 创建指令

```python
from friday.instruction import teach, match, list_instructions, remove

# 创建指令
teach(
    name="查看 Git 状态",
    trigger="看状态",
    actions=[
        {"command": "git status", "description": "查看仓库状态"},
        {"command": "git log --oneline -5", "description": "查看最近5条提交"},
    ],
    keywords=["git", "状态", "status"],
)

# 多步操作自动识别为 workflow 类型
```

### 5.2 指令匹配

```python
from friday.instruction import match

# 精确匹配
results = match("看状态")      # score=1.0

# 关键词匹配
results = match("查一下 git")  # score=0.67

# 不匹配
results = match("今天吃什么")  # 无结果
```

### 5.3 管理指令

```python
from friday.instruction import list_instructions, remove, reload

# 列出所有指令
instructions = list_instructions()

# 删除指令
remove("查看 Git 状态")

# 从文件系统重新加载
count = reload()
```

指令以 YAML 文件存储在 `~/.friday/instructions/` 下，可直接编辑。

---

## 6. 记忆系统

Friday 的记忆分两层：

### 6.1 结构化文件记忆

手动管理、Git 友好的长期记忆，存储在 `.specify/memory/` 下。

#### 决策记录

```python
from friday.memory import add_decision, list_decisions

add_decision(
    title="选择 Python 作为开发语言",
    decision="Python 生态丰富，适合快速迭代",
    context="MVP 阶段需要快速交付",
    status="已采纳",
)
```

存储位置：`.specify/memory/decisions.md`

#### 经验教训

```python
from friday.memory import add_lesson, list_lessons

add_lesson(
    title="数据库迁移要加事务",
    lesson="之前迁移失败导致数据丢失，以后必须用事务包裹",
    context="生产环境迁移",
)
```

存储位置：`.specify/memory/lessons-learned.md`

#### 项目宪法

编辑 `.specify/memory/constitution.md` 定义项目的基本规则和约束。

#### 搜索文件记忆

```python
from friday.memory import search_memories

results = search_memories("Python")
for r in results:
    print(f"[{r.source}] {r.content[:100]}")
```

### 6.2 动态记忆 (Mem0)

对话中自动提取和检索的记忆，适合偏好、习惯等碎片化信息。

> 注意：动态记忆需要额外配置 OpenAI 兼容的 LLM 端点。

---

## 7. 执行器

Friday 可以替你执行 Shell 命令。安全性分三级：

### 7.1 安全级别

| 级别 | 行为 | 命令示例 |
|------|------|----------|
| **safe** | 直接执行 | ls, pwd, cat, git, find, grep, tree |
| **confirm** | 首次需确认，之后自动信任 | python, node, curl |
| **dangerous** | 每次都需确认 | rm -rf, sudo, shutdown, mkfs |

### 7.2 信任管理

首次确认的命令会被自动标记为信任，后续直接执行。也可手动添加：

```python
from friday.executor import trust_command

trust_command("docker")  # 将 docker 标记为信任命令
```

信任记录存储在 `~/.friday/executor.db`。

### 7.3 执行历史

所有执行过的命令都有记录：

```python
from friday.executor import get_history_records

records = get_history_records(limit=10)
for r in records:
    print(f"[{r.safety_level}] {r.command} (exit={r.exit_code})")
```

历史记录保留 90 天，存储在 `~/.friday/executor.db`。

---

## 8. 数据目录

所有运行时数据存储在 `~/.friday/` 下：

```
~/.friday/
├── config.yaml           # LLM 配置
├── knowledge/
│   ├── notes/            # 知识笔记 (Markdown)
│   ├── fts.db            # FTS5 全文索引 (SQLite)
│   └── chroma/           # 向量索引 (ChromaDB)
├── instructions/         # 学到的指令 (YAML)
├── sessions/             # 会话历史 (JSON)
├── executor.db           # 执行历史 + 信任命令
└── logs/                 # 运行日志
```

项目内数据：

```
<project>/
├── .specify/memory/      # 文件记忆
│   ├── constitution.md   # 项目宪法
│   ├── decisions.md      # 决策记录
│   └── lessons-learned.md # 经验教训
└── .friday-memory/       # Mem0 动态记忆 (ChromaDB)
```

---

## 9. 常见问题

### Q: 首次启动报错 "LLM 未配置"

编辑 `~/.friday/config.yaml`，添加 API Key。参考 [1.2 配置 LLM](#12-配置-llm)。

### Q: 向量搜索不可用

向量搜索需要下载 BAAI/bge-m3 模型（约 2GB）。首次使用需网络通畅。下载完成后会缓存到本地。

如网络受限，FTS5 全文搜索仍然可用，可满足大部分搜索需求。

### Q: Mem0 动态记忆初始化失败

Mem0 内部使用 OpenAI API 做记忆提取。目前暂不支持智谱 API。文件记忆（决策、经验）不受影响。

### Q: 如何切换 AI 模型

修改 `~/.friday/config.yaml` 中的 `provider` 和对应配置：

```yaml
llm:
  provider: deepseek    # 切换为 deepseek
  providers:
    zhipu:
      api_key: xxx
      model: glm-4.7
    deepseek:
      api_key: yyy
      model: deepseek-chat
```

也可通过代码运行时切换：

```python
from friday.llm import switch_provider
switch_provider("deepseek")
```

### Q: 如何备份我的数据

```bash
# 备份所有运行时数据
cp -r ~/.friday/ ~/friday-backup/

# 备份项目内记忆
cp -r .specify/memory/ ~/friday-memory-backup/
```
