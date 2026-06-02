# Code Review Report

**Feature**: 双层记忆系统
**Date**: 2026-06-03
**Reviewer**: Code Reviewer Agent

## Summary

双层记忆系统的实现整体质量良好。四个源文件结构清晰，遵循了 adapter 模式，数据模型定义明确，函数职责单一。测试文件覆盖了文件记忆的核心 CRUD 路径。

存在 3 个需要修复的问题：(1) `files.py` 中 `MEMORY_DIR` 使用相对路径，运行时依赖 cwd；(2) `search_files` 的 `source` 字段值与数据模型规范不一致；(3) 测试的 fixture 在异常场景下缺少 cleanup 保证。此外有若干建议性改进。

## Checklist Results

| # | Check Item | Result | Notes |
|---|-----------|--------|-------|
| 1 | Spec compliance | CHANGES REQUIRED | source 字段值偏差；FR-009 存储路径有歧义；FR-004 分页未实现但 API contract 未要求 |
| 2 | Constitution compliance | PASS | 遵循个人化优先、本地优先、简洁实用原则；模块边界清晰"只管记忆的存取" |
| 3 | Architecture compliance | PASS | adapter 模式正确；模块调用关系与 CLAUDE.md 一致 |
| 4 | File size | PASS | 最大 186 行 (files.py)，均低于 200 行上限 |
| 5 | Function size | PASS | 所有函数均在 30 行以内 |
| 6 | Type annotations | PASS | 所有函数参数和返回值均有完整类型注解 |
| 7 | Adapter layer | PASS | dynamic.py 通过 `_build_llm_config()` 从 config adapter 获取 LLM 配置，未直接依赖 SDK 配置常量 |
| 8 | Storage layer | PASS | dynamic.py 封装 Mem0，files.py 封装文件 IO，adapter.py 只做委托 |
| 9 | Test coverage | CHANGES REQUIRED | 文件记忆测试充分；动态记忆测试全部 skip，实际只有数据类测试在运行 |
| 10 | Security | PASS | 无注入风险；文件路径硬编码不接收用户输入；query 参数仅做字符串匹配 |
| 11 | No over-engineering | PASS | 抽象层次恰当，无冗余设计 |
| 12 | No direct SDK calls | PASS | Mem0 通过 adapter 层封装，LLM 配置通过 config adapter 获取 |

## Findings

### CRITICAL (must fix)

None.

### IMPORTANT (should fix)

#### 1. files.py MEMORY_DIR 使用相对路径，运行时依赖 cwd

**File**: `/Users/tongliu/work/friday/src/friday/memory/files.py`, line 12

```python
MEMORY_DIR = Path(".specify/memory")
```

`Path(".specify/memory")` 是相对路径，解析结果取决于进程的当前工作目录。如果用户从 `~` 或其他非项目根目录运行 `friday`，文件记忆会写到错误位置。相比之下，`dynamic.py` 的 `MEMORY_DIR` 使用 `CONFIG_DIR.parent / ".friday-memory"` 是绝对路径。

**Spec reference**: FR-009 规定"文件记忆存储目录为 `.specify/memory/`"。data-model.md 进一步明确了 `.specify/memory/` 路径。但 `.specify/memory/` 本身隐含"项目根目录下"的语义，需要绝对路径才能正确表达。

**Suggestion**: 使用项目根目录定位，与 `dynamic.py` 的模式保持一致。例如：

```python
# 获取项目根目录（假设 src/friday/ 在项目内）
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
MEMORY_DIR = _PROJECT_ROOT / ".specify" / "memory"
```

或者通过 `config.py` 暴露项目根路径常量。

---

#### 2. search_files 的 source 字段值与数据模型规范不一致

**File**: `/Users/tongliu/work/friday/src/friday/memory/files.py`, line 101

```python
for path_name, source in [("decisions.md", "decision"), ("lessons-learned.md", "lesson")]:
```

`source` 字段使用了 `"decision"` 和 `"lesson"` 这两个具体类型名称，但 data-model.md 和 research.md 明确定义 `source` 字段的可选值为 `"dynamic"` / `"files"`：

> data-model.md: `source | str | 是 | 来源："dynamic" / "files"`
> research.md R003: `source: str  # "dynamic" / "files"`

**Impact**: 调用方无法通过 `source == "files"` 过滤文件记忆结果，必须知道具体的 `"decision"` / `"lesson"` 才能匹配，破坏了统一检索的抽象。

**Suggestion**: 将 source 改为 `"files"`，具体文件类型可放到 `metadata` 中：

```python
results.append(MemorySearchResult(
    source="files",
    content="## " + section.strip(),
    score=1.0,
    metadata={"file": path_name, "type": source},  # type 可以是 "decision"/"lesson"
))
```

---

#### 3. 测试 fixture 在异常路径下缺少 cleanup 保证

**File**: `/Users/tongliu/work/friday/tests/unit/test_memory_files.py`, lines 11-16

```python
@pytest.fixture
def isolated_files(tmp_path: Path) -> None:
    old_dir = files.MEMORY_DIR
    files.MEMORY_DIR = tmp_path
    yield
    files.MEMORY_DIR = old_dir
```

如果测试代码在 `yield` 之前抛出异常（例如 `tmp_path` 类型错误），`MEMORY_DIR` 不会被恢复。应使用 `try/finally` 确保 cleanup。此外，`files.MEMORY_DIR` 是模块级变量，并发测试存在竞争条件（虽然 pytest 默认不并发运行测试，但作为防御性编程仍需注意）。

**Suggestion**: 使用 `try/finally` 模式：

```python
@pytest.fixture
def isolated_files(tmp_path: Path) -> None:
    old_dir = files.MEMORY_DIR
    files.MEMORY_DIR = tmp_path
    try:
        yield
    finally:
        files.MEMORY_DIR = old_dir
```

或者使用 `monkeypatch`（pytest 内置 fixture）：

```python
@pytest.fixture
def isolated_files(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(files, "MEMORY_DIR", tmp_path)
```

### SUGGESTIONS (nice to have)

#### 4. `_append_entry` 函数名有误导性

**File**: `/Users/tongliu/work/friday/src/friday/memory/files.py`, line 48

函数名 `_append_entry` 暗示追加到文件末尾，但实际逻辑是 `entry + "\n" + content`，即前置插入。建议改名为 `_prepend_entry` 或 `_insert_entry_first`，使名称与行为一致。

---

#### 5. dynamic.py 的 `_memory_instance` 全局状态缺少重置机制

**File**: `/Users/tongliu/work/friday/src/friday/memory/dynamic.py`, lines 14, 37-43

`_memory_instance` 是模块级全局变量，初始化后无法重置。这会导致：
- 测试时无法隔离（`_memory_instance` 被第一个测试设置后，后续测试看到缓存实例）
- 配置变更后无法重新初始化

建议添加 `_reset_memory()` 函数用于测试：

```python
def _reset_memory() -> None:
    """重置 Mem0 实例（仅用于测试）"""
    global _memory_instance
    _memory_instance = None
```

---

#### 6. 动态记忆测试全部被 skip，实际运行覆盖率为零

**File**: `/Users/tongliu/work/friday/tests/unit/test_memory_dynamic.py`, lines 38-39, 52

```python
@pytest.mark.skip(reason="需要 LLM API 配置才能运行")
def test_add_and_search(self) -> None:
```

`TestMem0Integration` 下的两个测试均被 skip。`TestMemoryItem` 和 `TestMemorySearchResult` 只测试了数据类的字段赋值，没有测试实际的 CRUD 逻辑。

建议增加 mock-based 单元测试，不依赖 LLM API：

```python
from unittest.mock import patch, MagicMock

def test_add_memory_with_mock() -> None:
    mock_mem = MagicMock()
    mock_mem.add.return_value = {"results": [{"id": "test-id"}]}
    with patch("friday.memory.dynamic._get_memory", return_value=mock_mem):
        item = add_memory("test content")
        assert item.id == "test-id"
        assert item.content == "test content"
```

---

#### 7. dynamic.py 中 add_memory 在 Mem0 不可用时抛出 RuntimeError，但其他函数返回空值

**File**: `/Users/tongliu/work/friday/src/friday/memory/dynamic.py`, line 94

```python
def add_memory(content: str, metadata: dict[str, Any] | None = None) -> MemoryItem:
    m = _get_memory()
    if m is None:
        raise RuntimeError("动态记忆服务不可用")
```

对比 `search_memory`（返回 `[]`）、`list_memories`（返回 `[]`）、`delete_memory`（返回 `False`），`add_memory` 是唯一抛异常的函数。spec 的 Edge Cases 提到"动态记忆存储服务不可用时：返回降级结果"。建议保持一致性，要么所有函数都抛异常，要么 `add_memory` 也返回一个标识失败的对象。

---

#### 8. spec 中 FR-004 的"分页"需求与 API contract 不一致

**File**: `/Users/tongliu/work/friday/specs/006-dual-layer-memory/spec.md`, line 75

```
FR-004: 系统必须支持列出所有动态记忆（分页）
```

但 contracts/memory-api.md 的 `list_memories()` 没有分页参数，实现也没有分页。当前用户记忆量预计 < 1000 条（plan.md），不分页是合理的。建议更新 spec.md 的 FR-004，去掉"分页"或改为"按需支持分页"。

---

#### 9. research.md 提到 "YAML front matter" 但实现使用 Markdown 加粗字段

**File**: `/Users/tongliu/work/friday/specs/006-dual-layer-memory/research.md`, line 43

research.md 提到"使用 YAML front matter 存储元数据"，但实际实现用 `**字段**: 值` 的 Markdown 格式。当前的 Markdown 格式更简洁、更易编辑，是更好的选择。建议更新 research.md 使文档与实现一致。

## What Was Done Well

1. **Adapter 模式执行到位**: `adapter.py` 作为统一入口，委托给 `dynamic.py` 和 `files.py`，层次清晰，没有跨层调用。
2. **数据模型设计简洁**: `MemoryItem`、`MemorySearchResult`、`Decision`、`Lesson` 四个 dataclass 职责明确，字段精简。
3. **统一检索实现正确**: `search_memories()` 合并两层结果并按 score 降序排序，符合 spec 的 US3 要求。
4. **文件记忆的 Markdown 格式**: 格式清晰易读，人工编辑友好，支持 Git diff。解析逻辑使用正则分割，代码简洁。
5. **防御性编程**: `dynamic.py` 的 `_init_memory()` 捕获所有异常并返回 None，避免 Mem0 不可用时整个模块崩溃。
6. **公共 API 导出**: `__init__.py` 的 `__all__` 列表完整，与 contracts/memory-api.md 完全对齐。
7. **文件大小控制**: 所有源文件在 200 行以内，最大 186 行，远好于上限。

## Verdict

**CHANGES REQUIRED**

需要修复 3 个 Important 问题后重新审核：
1. `files.py` 的 `MEMORY_DIR` 改为绝对路径
2. `search_files` 的 `source` 字段值改为 `"files"` 以匹配数据模型规范
3. 测试 fixture 增加 cleanup 保证

此外建议补充 mock-based 动态记忆单元测试，将 `add_memory` 的异常处理与其他函数统一，并同步更新 research.md 中 YAML front matter 的描述。
