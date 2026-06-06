# Tasks: Friday 记忆系统重构

**Feature**: 011-memory-refactor
**Branch**: `011-memory-refactor`
**Plan**: [plan.md](plan.md) | **Spec**: [spec.md](spec.md)

## Implementation Strategy

MVP = Phase 1 + Phase 2（清理 + 核心改动），完成后 Friday 的记忆系统即可正常工作。Phase 3 和 Phase 4 为补全和收尾。

---

## Phase 1: 清理 — 移除文件记忆 (US3)

**Story Goal**: 移除不属于用户产品的文件记忆功能，明确记忆系统只服务于用户对话

**Independent Test**: 记忆模块对外接口中不存在决策记录、经验教训、项目宪法等文件记忆相关函数

### Tasks

- [X] T001 [G1] [P] [US3] 删除文件记忆模块 `src/friday/memory/files.py` 及其测试 `tests/unit/test_memory_files.py` 和 `tests/integration/test_memory_integration.py`
- [X] T002 [G1] [P] [US3] 精简 `src/friday/memory/adapter.py`：移除所有 `files.py` 导入和转发函数（`add_decision`, `list_decisions`, `add_lesson`, `list_lessons`, `get_constitution`），简化 `search_memories()` 为只调用 `_search_dynamic()`
- [X] T003 [G2] [US3] 更新 `src/friday/memory/__init__.py`：移除 `files.py` 相关导出，只导出 `adapter.py` 的动态记忆函数

---

## Phase 2: 核心改动 — 存储路径 + 上下文注入 (US1 + US2 + US4)

**Story Goal**: 修正记忆数据存储路径到 `~/.friday/memory/`，改用用户当前消息内容检索记忆

**Independent Test**: 记忆数据实际存储在 `~/.friday/memory/` 下；对话中用不同关键词能召回相关记忆

### Tasks

- [X] T004 [G3] [P] [US4] 修改 `src/friday/memory/dynamic.py`：将 `MEMORY_DIR` 从 `CONFIG_DIR.parent / ".friday-memory"` 改为 `CONFIG_DIR / "memory"`（即 `~/.friday/memory/`）
- [X] T005 [G3] [P] [US2] 修改 `src/friday/memory/dynamic.py`：统一 `search_memory()` 返回类型为 `list[MemorySearchResult]`，确保调用方使用 dataclass 属性访问而非字典访问
- [X] T006 [G4] [US1] 修改 `src/friday/cli/repl.py` 的 `_build_context()`：用 `session.messages[-1].content`（用户当前消息）作为检索查询替代硬编码的 `"用户偏好 习惯 设置"`，移除 stderr 重定向 hack，适配 `search_memory()` 的新返回类型
- [X] T007 [G4] [US2] 在 `src/friday/cli/repl.py` 的 `_build_context()` 中添加记忆注入上限（最多 5 条），过滤低相关度结果（score 阈值过滤）

---

## Phase 3: 测试 (US1 + US2)

**Story Goal**: 确保记忆系统的核心逻辑有自动化测试覆盖

**Independent Test**: 运行 `pytest tests/unit/test_memory_dynamic.py tests/unit/test_memory_context.py -v` 全部通过

### Tasks

- [X] T008 [G5] [P] [US1] 更新 `tests/unit/test_memory_dynamic.py`：移除 `TestMemorySearchResult` 中 `source="files"` 的测试，确保 `search_memory()` 返回类型为 `list[MemorySearchResult]` dataclass，新增测试：空记忆库返回空列表、初始化失败降级、MEMORY_DIR 指向 `~/.friday/memory/`
- [X] T009 [G5] [P] [US2] 新增 `tests/unit/test_memory_context.py`：测试 `_build_context()` 使用用户消息内容检索（而非硬编码关键词）、记忆注入上限 5 条、低相关度结果被过滤、检索异常时返回空 PromptContext

---

## Phase 4: 收尾 — 文档更新

**Story Goal**: 项目文档反映记忆系统的新架构

**Independent Test**: CLAUDE.md 中无"双层记忆"或"文件记忆"描述

### Tasks

- [X] T010 [G6] 更新 `CLAUDE.md`：移除"双层记忆系统"描述改为"动态记忆系统"，更新架构图中 memory/ 的描述，移除 `.specify/memory/` 和文件记忆相关的说明

---

## Parallel Groups

| Group | Tasks  | Depends On | Notes                              |
|-------|--------|------------|------------------------------------|
| G0    | —      | —          | 无 setup 任务                      |
| G1    | T001, T002 | —     | 删除 files.py 和精简 adapter.py 并行 |
| G2    | T003   | G1         | 更新 __init__.py，依赖 G1 完成     |
| G3    | T004, T005 | G2    | 修改 dynamic.py 的两个独立改动并行  |
| G4    | T006, T007 | G3    | 修改 repl.py 的两个独立改动并行     |
| G5    | T008, T009 | G4    | 测试任务并行                        |
| G6    | T010   | G5         | 文档更新最后执行                    |

**Max parallelism**: 2
**Total groups**: 7
