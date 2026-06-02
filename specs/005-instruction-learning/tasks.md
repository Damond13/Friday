# Tasks: 指令学习模块

**Input**: Design documents from `/specs/005-instruction-learning/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/instruction-api.md

**Tests**: CLAUDE.md 要求"测试覆盖核心逻辑"，测试任务在 Polish 阶段执行。

**Organization**: 按用户故事组织任务，每个故事可独立实现和测试。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行执行（不同文件，无依赖）
- **[Story]**: 所属用户故事（US1, US2, US3, US4）
- 描述包含精确文件路径

---

## Phase 1: Setup（项目初始化）

**Purpose**: 创建模块文件结构

- [x] T001 在 src/friday/instruction/ 下创建 models.py, store.py, matcher.py, adapter.py 空文件，在 tests/unit/ 下创建 test_instruction_store.py, test_instruction_matcher.py 空文件

---

## Phase 2: Foundational（阻塞性前置条件）

**Purpose**: 所有用户故事依赖的数据模型定义

**⚠️ CRITICAL**: 类型定义是所有故事的前置依赖

- [x] T002 定义数据模型在 src/friday/instruction/models.py：InstructionType 枚举（single/workflow/conditional），Action 数据类（command, description, confirm），Instruction 数据类（name, trigger, type, description, keywords, actions, created_at, updated_at），MatchResult 数据类（instruction, score, match_type）

**Checkpoint**: 数据模型定义完成，所有后续任务可引用类型

---

## Phase 3: User Story 1 - 对话式教学 (Priority: P1) 🎯 MVP

**Goal**: 用户可通过 teach() 创建指令并保存为 YAML 文件

**Independent Test**: 调用 teach(name="deploy", trigger="deploy", actions=[{"command": "./deploy.sh"}]) 成功创建 YAML 文件，再 load() 验证内容正确

- [x] T003 [US1] 实现 YAML 存储层在 src/friday/instruction/store.py：_slugify() 触发词转文件名，save() 写入 YAML，load() 读取单条，load_all() 扫描目录读取全部，delete() 删除文件，ensure_dir() 确保目录存在。存储路径 ~/.friday/instructions/
- [x] T004 [US1] 实现 teach() 在 src/friday/instruction/adapter.py：验证参数（trigger ≥ 2 字符，actions 非空）→ 构建 Instruction 对象 → 调用 store.save() → 返回 Instruction。同名指令时覆盖旧文件

**Checkpoint**: teach() 可正常创建指令文件并加载验证

---

## Phase 4: User Story 2 - 指令匹配 (Priority: P2)

**Goal**: 用户输入文本后，系统返回匹配到的指令列表（按匹配度排序）

**Independent Test**: 预存若干指令，调用 match("帮我 deploy") 返回精确匹配结果

- [x] T005 [US2] 实现匹配引擎在 src/friday/instruction/matcher.py：match_instructions() 接收文本和指令列表，执行两级匹配 — 精确匹配（trigger 完全出现在输入分词中，score=1.0）和关键词匹配（Jaccard 相似度，score=0.0~1.0），阈值 ≥ 0.3，返回 list[MatchResult] 按评分降序
- [x] T006 [US2] 实现 match() 在 src/friday/instruction/adapter.py：调用 store.load_all() 获取全部指令 → 调用 matcher.match_instructions() → 返回排序后的 list[MatchResult]，支持 top_k 参数限制返回数量

**Checkpoint**: 精确匹配和关键词匹配均可正常工作

---

## Phase 5: User Story 3 - 指令管理 (Priority: P3)

**Goal**: 用户可查看所有指令列表、删除指令、重新加载

**Independent Test**: 创建 3 条指令后 list_instructions() 返回 3 条，remove("deploy") 后返回 2 条

- [x] T007 [US3] 实现管理接口在 src/friday/instruction/adapter.py：list_instructions() 返回全部指令按名称排序，remove() 调用 store.delete() 并返回是否成功，reload() 调用 store.load_all() 刷新内存缓存并返回加载数量

**Checkpoint**: 列表、删除、重新加载均可正常工作

---

## Phase 6: User Story 4 - 多步工作流 (Priority: P4)

**Goal**: 支持创建多步工作流和条件分支指令

**Independent Test**: 创建包含 3 个步骤的 workflow 指令，加载后步骤顺序正确

- [x] T008 [US4] 在 src/friday/instruction/adapter.py 的 teach() 中增强类型处理：当 actions 数量 > 1 时自动推断 type 为 workflow（若未显式指定），验证 conditional 类型需包含描述信息，确保多步指令的 actions 顺序在 YAML 中保持

**Checkpoint**: 多步工作流和条件分支类型可正常创建和加载

---

## Phase 7: Polish & Cross-Cutting

**Purpose**: 公共 API 导出、单元测试、端到端验证

- [x] T009 [P] 实现公共 API 导出在 src/friday/instruction/__init__.py：导出 teach, match, list_instructions, remove, reload, Instruction, Action, MatchResult, InstructionType，定义 __all__
- [x] T010 [P] 编写存储层单元测试在 tests/unit/test_instruction_store.py：测试 save/load 正确性、load_all 扫描、delete 删除、YAML 格式错误跳过、slug 生成、中文触发词处理
- [x] T011 [P] 编写匹配引擎单元测试在 tests/unit/test_instruction_matcher.py：测试精确匹配（score=1.0）、关键词匹配（score>0）、无匹配返回空、多结果按评分排序、top_k 限制
- [x] T012 按 quickstart.md 的 5 个验证场景端到端验证

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 无依赖，立即开始
- **Foundational (Phase 2)**: 依赖 Setup 完成 — 阻塞所有用户故事
- **US1 (Phase 3)**: 依赖 Foundational — MVP 核心
- **US2 (Phase 4)**: 依赖 US1（在 adapter.py 基础上增加匹配流程）
- **US3 (Phase 5)**: 依赖 US1（在 adapter.py 基础上增加管理接口）
- **US4 (Phase 6)**: 依赖 US1（在 adapter.py 基础上增强类型处理）
- **Polish (Phase 7)**: 依赖 US1-US4 全部完成

### User Story Dependencies

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational)
    ↓
Phase 3 (US1 - 教学) 🎯 MVP
    ↓
    ├── Phase 4 (US2 - 匹配)
    ├── Phase 5 (US3 - 管理)
    └── Phase 6 (US4 - 工作流)
         ↓
    Phase 7 (Polish)
```

### Parallel Opportunities

- Phase 7: T009, T010, T011 可并行（不同文件）

---

## Implementation Strategy

### MVP First（仅 User Story 1）

1. 完成 Phase 1: Setup
2. 完成 Phase 2: Foundational
3. 完成 Phase 3: US1 教学
4. **验证**: teach() 创建指令 → YAML 文件存在 → load() 内容正确
5. 此时 Friday 已具备最基本的指令存储能力

### Incremental Delivery

1. Setup + Foundational → 数据模型就绪
2. US1 教学 → **MVP 可用！**
3. US2 匹配 → 匹配能力
4. US3 管理 → 管理能力
5. US4 工作流 → 多步支持
6. Polish → 测试 + 导出 + 验证
