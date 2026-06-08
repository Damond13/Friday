# Code Review Report

**Feature**: 知识库添加工具 (knowledge_add tool)
**Date**: 2026-06-08
**Reviewer**: Reviewer Agent

## Summary

Implementation faithfully follows spec and plan. A new `knowledge_add` tool definition and its executor were added to the LLM module with minimal, focused changes. Tests cover both the schema contract and the executor's boundary conditions. One notable structural issue found (executor placement), along with a few minor suggestions.

## Checklist Results

| # | Check Item | Result | Notes |
|---|-----------|--------|-------|
| 1 | Spec compliance | PASS | FR-001 through FR-007 all addressed |
| 2 | Constitution compliance | PASS | No violations of any principle |
| 3 | Architecture compliance | PASS (see note) | Follows existing pattern; minor structural concern noted in Findings |
| 4 | File size | PASS | tools.py: 147 lines, executors.py: 165 lines, test_tools.py: 69, test_executors.py: 53 |
| 5 | Function size | PASS | `_exec_knowledge_add`: 19 lines (well under 30-line limit) |
| 6 | Type annotations | PASS | All functions properly annotated |
| 7 | Adapter layer | PASS | All LLM calls through llm/adapter; knowledge calls through knowledge/adapter |
| 8 | Storage layer | PASS | `add_note` called via `friday.knowledge.adapter.add_note`, never direct storage |
| 9 | Test sync | PASS | tools.py tests updated; executors.py boundary tests added |
| 10 | Test coverage | PASS | Schema validation + 6 boundary tests covering empty, whitespace, truncation, success |
| 11 | Security | PASS | Input stripped, no injection risk, title truncation prevents abuse |
| 12 | No over-engineering | PASS | Minimal change, no unnecessary abstractions |
| 13 | No direct SDK calls | PASS | All external calls through adapter layer |

## Findings

### Suggestion (S1): `MAX_TITLE_LEN` constant placement

**File**: `src/friday/llm/executors.py:136`

`MAX_TITLE_LEN = 100` is defined between the last executor function and the `_register` block. The section header comment on line 134 reads "注册所有执行器", but the constant and `_exec_knowledge_add` function are interleaved between that comment and the actual registration calls. This makes the structure slightly confusing when scanning the file.

**Recommendation**: Move `MAX_TITLE_LEN` to the top of the file with other module-level constants (near line 10-13 where types are defined), or add a clear section header `# -- knowledge_add --` before line 138 matching the pattern of other executors. The other executors each have their own section header (e.g., `# -- shell_execute --`, `# -- knowledge_search --`), but `_exec_knowledge_add` lacks one.

### Suggestion (S2): Truncation silence

**File**: `src/friday/llm/executors.py:148-149`

When title is truncated, the success message shows the truncated title without indicating it was shortened. The user (or LLM) sees the shortened title and may not realize content was lost.

```python
if len(title) > MAX_TITLE_LEN:
    title = title[:MAX_TITLE_LEN]
```

**Recommendation**: Consider appending a truncation indicator in the success output, e.g., `f"已添加笔记 (id: {note.id})「{note.title}」"` could note "(标题已截断)" when truncation occurred. This is not a spec requirement (FR-007 only says "自动截断到合理长度"), so this is purely a UX suggestion for a future iteration.

### Suggestion (S3): No mock in executor integration tests

**File**: `tests/unit/test_executors.py:37-45`

`test_successful_add` and `test_long_title_truncated` call `knowledge_add` which invokes `friday.knowledge.adapter.add_note` against the real filesystem. This makes them integration tests rather than pure unit tests. They create actual note files in `~/.friday/knowledge/notes/`.

**Recommendation**: For true unit test isolation, mock `friday.knowledge.adapter.add_note` with `unittest.mock.patch`. However, given the project's testing philosophy ("测试覆盖核心逻辑，CLI 层不写测试") and the small scope, the current approach is acceptable. Marking these as integration tests in the file docstring would improve clarity.

### Good Practices Noted

1. **Consistent pattern**: The implementation mirrors `KNOWLEDGE_SEARCH` / `_exec_knowledge_search` exactly, maintaining codebase consistency. The diff is clean and predictable.

2. **Defensive input handling**: `title` and `content` are `.strip()`-ed before validation, catching whitespace-only inputs (lines 141-142). This covers the edge case mentioned in spec's Edge Cases section.

3. **Proper error propagation**: Generic exceptions are caught and returned as `ToolResult(success=False, ...)` with meaningful messages, matching the existing executor pattern and satisfying FR-005.

4. **Correct tags default**: `tags = arguments.get("tags") or []` (line 143) handles both missing and null values cleanly.

5. **Test organization**: Boundary tests are well-structured with a dedicated test class and a helper `_run()` function, making the async test code readable.

6. **No scope creep**: The diff is minimal -- only 73 insertions across 4 source files, with zero changes to knowledge/, memory/, or cli/ modules. This matches the plan's "不改动" list exactly.

## Questions for Developer

None. The implementation is straightforward and all spec requirements are clearly addressed.

## Verdict

**APPROVED**

The implementation is clean, minimal, and spec-compliant. All 7 functional requirements are met, the architecture follows established patterns, and tests cover the critical paths. The three suggestions above (section header placement, truncation feedback, test type clarity) are all nice-to-have improvements with no functional impact. No changes required before merge.
