# 任务清单：CLI 交互壳

**输入**: 设计文档 `/specs/002-cli-shell/`

**前置条件**: plan.md, spec.md, data-model.md, contracts/cli-commands.md

**组织方式**: 按用户故事分组，每个故事可独立实现和测试

## 格式说明

- **[P]**: 可并行执行（不同文件，无依赖）
- **[USx]**: 所属用户故事编号

---

## Phase 1: 项目初始化

**目的**: 创建 CLI 模块文件结构和依赖

- [x] T001 [P] 创建 display.py 输出格式化模块骨架 in src/friday/cli/display.py
- [x] T002 [P] 创建 session.py 会话存储模块骨架 in src/friday/cli/session.py
- [x] T003 [P] 创建 slash.py 斜杠命令模块骨架 in src/friday/cli/slash.py
- [x] T004 [P] 创建 repl.py REPL 循环模块骨架 in src/friday/cli/repl.py
- [x] T005 创建 app.py 入口模块，定义 Typer app 和 main() 函数 in src/friday/cli/app.py
- [x] T006 更新 cli/__init__.py 导出公共接口 in src/friday/cli/__init__.py
- [x] T007 添加 prompt-toolkit 依赖到 pyproject.toml in pyproject.toml

---

## Phase 2: 基础层（阻塞性前置）

**目的**: 所有用户故事共用的基础设施，必须先完成

- [x] T008 实现 Session 和 Message 数据类，支持 JSON 序列化/反序列化 in src/friday/cli/session.py
- [x] T009 实现 save_session() 保存会话到 ~/.friday/sessions/ in src/friday/cli/session.py
- [x] T010 实现 load_session() 按 ID 加载会话 in src/friday/cli/session.py
- [x] T011 实现 list_sessions() 按时间倒序列出历史会话 in src/friday/cli/session.py
- [x] T012 实现 create_session() 创建新会话（UUID + 时间戳） in src/friday/cli/session.py
- [x] T013 实现 CommandResult 数据类和 dispatch() 命令分发函数 in src/friday/cli/slash.py
- [x] T014 实现 /help、/exit、/save、/history、/load 五个命令处理函数 in src/friday/cli/slash.py
- [x] T015 实现 show_welcome() 欢迎信息和 show_error() 错误显示 in src/friday/cli/display.py
- [x] T016 实现 show_save_success() 和 show_history_list() 输出格式化 in src/friday/cli/display.py

---

## Phase 3: 用户故事 1 - 对话交互 (P1) 🎯 MVP

**目标**: 用户启动 `friday` 进入交互模式，能进行多轮流式对话

**独立测试**: 启动 `friday`，看到欢迎信息，输入问题收到流式回复，输入 exit 退出

- [x] T017 [US1] 实现 REPL 主循环 run_repl()：初始化 PromptSession，循环读取输入，分发到 LLM 或命令 in src/friday/cli/repl.py
- [x] T018 [US1] 实现 stream_chat() 调用 llm.chat_stream() 流式输出到 Rich Console in src/friday/cli/repl.py
- [x] T019 [US1] 实现 Ctrl+C 处理：中断流式输出回到提示符，连续两次退出 in src/friday/cli/repl.py
- [x] T020 [US1] 实现 handle_input() 统一输入分发：斜杠命令 → slash.dispatch()，其他 → stream_chat() in src/friday/cli/repl.py
- [x] T021 [US1] 实现 main() 入口：message 参数为 None 时调用 run_repl() in src/friday/cli/app.py

**检查点**: `friday` 启动交互模式，能流式对话，exit 退出

---

## Phase 4: 用户故事 2 - 单次执行 (P1)

**目标**: 用户运行 `friday "问题"` 快速获取回复后自动退出

**独立测试**: 运行 `friday "你好"`，输出回复后程序自动退出

- [x] T022 [US2] 实现 run_single() 单次执行函数：调用 llm.chat()，输出回复，退出 in src/friday/cli/app.py
- [x] T023 [US2] 实现 API Key 未配置检测：调用 get_llm_config() 失败时显示配置引导 in src/friday/cli/app.py
- [x] T024 [US2] 在 main() 中添加 message 参数分发：有值时调用 run_single() in src/friday/cli/app.py

**检查点**: `friday "你好"` 单次执行并退出

---

## Phase 5: 用户故事 3 - 斜杠命令 (P2)

**目标**: 用户在交互模式中使用 /help、/save 等结构化命令

**独立测试**: 进入交互模式，/help 显示命令列表，/save 保存成功

- [x] T025 [US3] 在 REPL 循环中接入 slash.dispatch()，处理 CommandResult 的 should_exit 标志 in src/friday/cli/repl.py

**检查点**: /help、/save、/exit 命令正常工作（命令处理函数已在 Phase 2 实现）

---

## Phase 6: 用户故事 4 - 会话管理 (P3)

**目标**: 用户能保存/列出/恢复历史会话

**独立测试**: 对话后 /save，退出重启后 /history 看到，/load 恢复

- [x] T026 [US4] 在 REPL exit 时自动保存会话（调用 session.save_session()） in src/friday/cli/repl.py
- [x] T027 [US4] 实现 /history 输出格式化：编号 + 时间 + 首句摘要 in src/friday/cli/slash.py
- [x] T028 [US4] 实现 /load 恢复会话：加载历史消息到当前 messages 列表 in src/friday/cli/slash.py

**检查点**: /save、/history、/load 完整流程可用

---

## Phase 7: 收尾与测试

**目的**: 单元测试和代码质量

- [x] T029 [P] 编写 session.py 单元测试：创建/保存/加载/列表 in tests/unit/test_session.py
- [x] T030 [P] 编写 slash.py 单元测试：分发逻辑、各命令处理 in tests/unit/test_slash.py
- [x] T031 运行全量测试，确保通过 in tests/
- [x] T032 更新 __init__.py 确保公共导出完整 in src/friday/cli/__init__.py

---

## 依赖与执行顺序

### 阶段依赖

- **Phase 1**: 无依赖，立即开始
- **Phase 2**: 依赖 Phase 1 完成 — 阻塞所有用户故事
- **Phase 3-6**: 依赖 Phase 2 完成，按优先级顺序执行
- **Phase 7**: 所有用户故事完成后

### 用户故事依赖

- **US1 (对话交互)**: Phase 2 后可开始，无其他故事依赖
- **US2 (单次执行)**: Phase 2 后可开始，依赖 app.py 入口（与 US1 共用）
- **US3 (斜杠命令)**: 依赖 US1 的 REPL 循环
- **US4 (会话管理)**: 依赖 US1 的 REPL 循环和 US3 的 /save 命令

### 并行机会

- Phase 1 全部任务可并行（T001-T004 不同文件）
- Phase 2 的 session 和 slash 可并行（T008-T012 vs T013-T014）
- Phase 7 的两个测试文件可并行（T029、T030）

---

## 实现策略

### MVP 最小可用（US1 + US2）

1. Phase 1 → Phase 2 → Phase 3 → Phase 4
2. 验证：交互模式 + 单次执行都能工作
3. 此时已有可用产品

### 增量交付

1. MVP（US1+US2）→ 基础对话功能
2. +US3 → 斜杠命令支持
3. +US4 → 会话持久化
4. +Phase 7 → 测试覆盖
