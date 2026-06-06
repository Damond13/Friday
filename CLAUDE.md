# Friday — 个人 AI 助手

## 项目定位
Friday 是一个本地 CLI 工具，能记住你教它的知识，学会你教它的操作，并自动替你执行。
核心差异化：深度个人化 + 自然学习 + 情境感知。

## 技术栈
- Python 3.13 + Typer + Rich
- LLM: 智谱 API + DeepSeek API（可切换）
- 存储: SQLite + ChromaDB + 本地文件系统
- 记忆: Mem0（动态）+ 文件记忆（结构化）
- 开发: Claude Code + spec-kit SDD 工作流

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
├── bugs/                        # 缺陷报告（bugfix 产出）
├── src/friday/                  # 源代码
│   ├── cli/                     # 交互壳
│   ├── knowledge/               # 知识库
│   ├── executor/                # 执行器
│   ├── instruction/             # 指令学习
│   ├── memory/                  # 双层记忆系统
│   ├── llm/                     # LLM 调用层
│   └── config.py                # 全局配置
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
  2. **ChromaDB 语义索引** — 向量检索，模糊/语义匹配
  3. **RAG 问答** — 检索 + LLM 综合，最智能但最慢
- 自动监控目录，文件变化自动更新索引

### 执行器 (executor/)
- Shell 直接执行（无容器隔离）
- 安全策略分级：安全指令直接执行 / 新指令首次确认 / 危险指令每次确认
- 全盘文件访问权限
- 输出策略：短输出直接显示，长输出 AI 总结

### 指令学习 (instruction/)
- 对话式教学（"以后每次我说xxx，你就做xxx"）
- YAML 配置文件存储，可直接编辑
- 支持类型：单步指令 / 多步工作流 / 条件分支

### 双层记忆系统 (memory/)
- **Mem0 动态记忆（自动）** — 对话中自动提取，语义检索，存于 `.friday-memory/`
- **结构化文件记忆（手动+Git管理）** — constitution.md / decisions.md / lessons-learned.md

### LLM 调用层 (llm/)
- 多模型可切换（智谱 GLM / DeepSeek）
- System Prompt 组装：用户记忆 + 知识 + 指令
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

## CodeGraph 提醒

项目已配置 CodeGraph 索引（`.codegraph/`），适合以下场景时优先使用：
- 查函数/类的调用链和影响范围（`codegraph_trace`, `codegraph_impact`）
- 跨模块依赖分析（`codegraph_callers`, `codegraph_callees`）
- 快速定位某个概念的代码上下文（`codegraph_context`）
- 了解文件结构和符号概览（`codegraph_files`, `codegraph_search`）

全局统计类任务（行数、文件列表、模块概览）用常规工具更直接。

## 编码规范

- 每个文件不超过 200 行，函数不超过 30 行
- 类型注解必须加
- 所有外部调用走 adapter 层，不直接依赖第三方 SDK
- 测试覆盖核心逻辑，CLI 层不写测试
- **测试策略** — 按风险评估决定测试范围：高风险功能必做，低风险可选。测试类型包括单元测试和集成测试。实现后补测试，在 implement/fix 节点写完测试后立即运行该模块测试确认通过。禁止自动运行全量测试（`pytest tests/`），但必须运行当前模块测试（如 `pytest tests/test_vector.py -v`）
- 所有代码通过 `uv run` 执行，测试用 pytest
- **目录结构清晰** — 新增文件必须归入合适的目录，保持项目结构清晰、分类明确。禁止在项目根目录随意放置文件；如无合适目录，先新建再放置
- **测试同步维护** — 修改模块代码时，必须同步检查该模块的自动化测试是否需要更新。包括：新增功能补测试、删除功能删测试、接口变更改测试
- **工具可复用** — 新增的脚本/工具必须设计为可复用、可重复执行，不能是一次性产物。要求：命令行可调用（带参数）、输出结构化、纳入 `scripts/` 目录统一管理
- **禁止自动跑全量测试** — SDD 工作流中所有 Agent 不得自动运行 `pytest tests/ -v`，只有用户明确要求时才执行
- **提交不加 Co-Authored-By 署名** — git commit message 不添加 Claude 协作署名

## 数据存储

- 运行时数据：`~/.friday/`（config.yaml, knowledge/, instructions/, sessions/, indexes/, logs/）
- 项目内数据：`.friday-memory/`（Mem0 ChromaDB）
- 工程化数据：`.specify/`（spec-kit SDD 工作流）
- 缺陷数据：`bugs/`（缺陷修复流程）

## 开发工作流

使用 spec-kit SDD 工作流：

```
specify → clarify → plan → tasks → implement → review
                                                        ↓
                                                   APPROVED?
                                                  ↓ Yes    ↓ No
                                                  ↓    CHANGES REQUIRED
                                            合并到 main    修复 → 再 review
                                                  ↓
                                            推送远程 → 删除功能分支
```

### 工作流各阶段职责

- **specify** — 根据用户描述生成功能规格文档（spec.md）
- **clarify** — 大模型读取 spec，识别疑问点和模糊之处，逐一向用户提问，用户确认或澄清后回写到 spec
- **plan** — 基于确认后的 spec 生成技术实施方案
- **tasks** — 将方案拆解为可执行任务，支持并行分组
- **implement** — 按任务顺序/并行执行实现
- **review** — 独立子 Agent 审核代码，确认通过后合并

### 工作流规则

1. **文档生成前确认** — spec/plan/tasks/research 等文档生成前，必须展示草稿并等用户确认后再写入
2. **文档使用中文** — 所有 spec/plan/tasks/research 等文档内容使用中文（标题、描述、说明），代码变量名用英文
3. **每阶段必须等用户确认** — specify → clarify → plan → tasks → implement → review 每个阶段产出后，必须暂停并等用户明确确认（如"确认"、"没问题"、"继续"），不能自动进入下一阶段。用户有权修改任何内容后才继续
4. **审核上下文隔离** — 代码审核（/speckit.review）必须通过 Agent 工具启动独立子 Agent 执行，不在主会话中直接审核
5. **审核角色选择** — 使用 `superpowers:code-reviewer` 子 Agent 类型执行审核，在 prompt 中附加 `.claude/agents/reviewer.md` 的检查项作为额外约束
6. **合并清理流程** — review APPROVED 后：合并到 main → 推送远程 → 删除功能分支
7. **优先借鉴开源方案** — 开发新功能前，必须先调研开源项目（通过 WebSearch / WebFetch），找到可借鉴的方案或可直接复用的库，避免重复造轮子。调研结果写入 spec 的"开源借鉴"章节
8. **测试必须同步** — tasks 阶段必须包含测试任务（按风险评估决定范围），implement 阶段实现后补测试并运行该模块测试确认通过，review 阶段检查测试覆盖

## 缺陷修复流程

使用 bugfix 工作流，解决"盲目修补"和"头痛医头"的问题：

```
report → diagnose → fixplan → fix → verify
```

### 缺陷修复各阶段职责

- **report** — 采集缺陷现象、环境信息、复现步骤（`/bugfix.report`）
- **diagnose** — 根因诊断，强制调研开源方案，判断代码级还是方案级问题（`/bugfix.diagnose`）
- **fixplan** — 设计修复方案，面向长期影响和可扩展性，非临时补丁（`/bugfix.fixplan`）
- **fix** — 按 fixplan 执行修复，不扩大范围（`/bugfix.fix`）
- **verify** — 验证修复有效，检查无回归（`/bugfix.verify`）

### 缺陷修复规则

1. **先诊断再动手** — 禁止跳过 diagnose 直接改代码
2. **调研必须做** — diagnose 阶段必须搜索开源社区的同类问题和解决方案
3. **允许换方案** — 如果 diagnose 判断为方案级问题，转入 SDD 新功能流程，不要在错误方案上修补
4. **面向长期** — fixplan 必须评估改动对可扩展性和未来功能的影响
5. **范围不蔓延** — fix 严格按 fixplan 执行，不加塞不扩大
6. **测试必须同步** — fixplan 必须包含测试更新评估，fix 阶段实现后补测试并运行该模块测试确认通过，verify 阶段确认测试已更新
7. **诚实验证** — 无法复现的 bug 标注验证局限性，不声称已验证
8. **每阶段等确认** — 和 SDD 流程一样，每个阶段产出后暂停等用户确认

### 缺陷数据存储

- 缺陷报告：`bugs/<编号>-<短名>/`（bug-report.md, diagnosis.md, fixplan.md, verify-report.md）
- 指针文件：`.specify/bugfix.json`
