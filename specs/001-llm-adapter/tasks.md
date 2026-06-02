# 任务列表：LLM 统一适配层

**输入**：设计文档来自 `/specs/001-llm-adapter/`
**前置条件**：plan.md（必需），spec.md（必需）

## 阶段 1：项目初始化

**目的**：创建模块结构和安装依赖

- [ ] T001 创建 llm 模块目录结构和 __init__.py 在 src/friday/llm/
- [ ] T002 添加依赖项（openai, pyyaml）到 pyproject.toml

---

## 阶段 2：基础设施（阻塞前置）

**目的**：所有用户故事共享的配置加载和错误类型

**⚠️ 关键**：此阶段完成前，不能开始任何用户故事

- [ ] T003 [P] 实现配置加载器，读取 ~/.friday/config.yaml 在 src/friday/config.py
- [ ] T004 [P] 定义自定义异常（LLMConnectionError, LLMAuthError, LLMResponseError）在 src/friday/llm/adapter.py

**检查点**：配置加载和错误类型就绪

---

## 阶段 3：用户故事 1 - 基础对话 (优先级: P1) 🎯 MVP

**目标**：用户发消息，Friday 通过 LLM 返回回复

**独立测试**：发送"你好"，收到非空文本回复

- [ ] T005 [P] [US1] 定义 ProviderConfig 和 Message 数据类 在 src/friday/llm/adapter.py
- [ ] T006 [US1] 实现 get_client() 工厂函数，返回配置好的 OpenAI 客户端 在 src/friday/llm/adapter.py
- [ ] T007 [US1] 实现 chat() 函数，支持消息发送和错误包装 在 src/friday/llm/adapter.py
- [ ] T008 [US1] 将 OpenAI SDK 异常包装为自定义异常 在 src/friday/llm/adapter.py

- [ ] T009 [P] [US1] 编写单元测试，测试 get_client() 和 chat()，mock OpenAI SDK 在 tests/unit/test_adapter.py

**检查点**：chat() 可以正常发送消息并收到回复

---

## 阶段 4：用户故事 2 - 模型切换 (优先级: P2)

**目标**：运行时切换 provider 和覆盖模型版本

**独立测试**：switch_provider("deepseek") 后 chat() 请求发送到正确的 API

- [ ] T009 [US2] 实现 switch_provider() 和 get_current_provider() 在 src/friday/llm/adapter.py
- [ ] T010 [US2] 实现 get_current_model() 和 chat() 的 model 覆盖参数 在 src/friday/llm/adapter.py

- [ ] T011 [US2] 在 test_adapter.py 添加 switch_provider() 和 model 覆盖参数测试

**检查点**：可以运行时切换 provider 和覆盖模型

---

## 阶段 5：用户故事 3 - 上下文组装 (优先级: P3)

**目标**：System prompt 自动注入用户记忆、知识、指令

**独立测试**：build_system_prompt() 返回包含偏好信息的完整 prompt

- [ ] T011 [P] [US3] 定义 PromptContext 数据类 在 src/friday/llm/prompts.py
- [ ] T012 [US3] 实现 build_system_prompt() 在 src/friday/llm/prompts.py
- [ ] T013 [US3] 将 prompt 组装集成到 chat() 在 src/friday/llm/adapter.py

- [ ] T015 [US3] 编写单元测试，测试 build_system_prompt() 在 tests/unit/test_prompts.py

**检查点**：System prompt 包含用户上下文信息

---

## 阶段 6：用户故事 4 - 工具调用 (优先级: P4)

**目标**：LLM 通过 function calling 触发 Shell/文件/知识库操作

**独立测试**：chat() 返回包含 tool_calls 的 LLMResponse

- [ ] T014 [P] [US4] 定义 ToolDefinition、ToolCall 数据类 在 src/friday/llm/tools.py
- [ ] T015 [US4] 实现 get_tool_definitions()，包含 shell/文件/知识库工具 在 src/friday/llm/tools.py
- [ ] T016 [US4] 为 chat() 添加工具调用支持 在 src/friday/llm/adapter.py
- [ ] T017 [US4] 实现 chat_stream() 流式输出 在 src/friday/llm/adapter.py

- [ ] T020 [US4] 编写单元测试，测试工具定义 schema 在 tests/unit/test_tools.py

**检查点**：工具调用和流式输出全部就绪

---

## 阶段 7：收尾与横切关注点

**目的**：模块导出和清理

- [ ] T021 配置公开 API 导出 在 src/friday/llm/__init__.py

---

## 依赖与执行顺序

### 阶段依赖

- **初始化（阶段 1）**：无依赖，立即开始
- **基础设施（阶段 2）**：依赖阶段 1
- **US1（阶段 3）**：依赖阶段 2 — MVP 核心功能
- **US2（阶段 4）**：依赖阶段 3（扩展 adapter）
- **US3（阶段 5）**：依赖阶段 2（需要 prompts.py）
- **US4（阶段 6）**：依赖阶段 3（扩展 chat()）
- **收尾（阶段 7）**：依赖阶段 6

### 并行机会

- T003 和 T004 可并行（不同文件）
- T005 和 T011 可并行（不同文件）
- T014 可与其他任务并行（不同文件 tools.py）

### 实施策略

**MVP 优先（仅 US1）**：
1. 完成阶段 1（初始化）
2. 完成阶段 2（基础设施）
3. 完成阶段 3（基础对话）
4. **暂停验证**：测试 chat() 是否能正常工作
5. 确认后继续 US2-US4

**增量交付**：
1. 初始化 + 基础设施 → 基础就绪
2. + US1 → 基础对话可用（MVP！）
3. + US2 → 模型切换可用
4. + US3 → 上下文组装可用
5. + US4 → 工具调用和流式输出可用
