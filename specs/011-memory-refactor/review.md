# Code Review Report

**Feature**: 011-memory-refactor (Friday 记忆系统重构)
**Date**: 2026-06-06
**Reviewer**: Reviewer Agent

## Summary

The implementation successfully delivers the core refactoring: removing the file memory layer, simplifying the memory module to only dynamic memory (Mem0), fixing the storage path from `~/.friday-memory/` to `~/.friday/memory/`, and replacing hardcoded search keywords with user message content. The code is clean, well-typed, and has appropriate test coverage. There are a few residual issues -- two stale references in CLAUDE.md, a misleading docstring on `MemorySearchResult.source`, and a duplicate line in CLAUDE.md -- that should be addressed before merge.

## Checklist Results

| # | Check | Result | Notes |
|---|-------|--------|-------|
| 1 | Spec compliance | ❌ | FR-001 partially violated: `MemorySearchResult.source` docstring still references `"files"`; CLAUDE.md lines 11 and 21 still mention file memory |
| 2 | Constitution compliance | ✅ | No violations. All five principles pass per plan's constitution check |
| 3 | Architecture compliance | ✅ | memory/ only handles memory CRUD. No cross-boundary concerns |
| 4 | File size | ✅ | All files under 200 lines. Largest is dynamic.py at 195 lines |
| 5 | Function size | ✅ | All functions under 30 lines |
| 6 | Type annotations | ✅ | All public functions have complete type annotations. Dataclasses use typed fields |
| 7 | Adapter layer | ✅ | LLM config access goes through `get_llm_config()`. Mem0 is only imported inside `dynamic.py` |
| 8 | Storage layer | ✅ | All memory data ops go through `dynamic.py` functions, surfaced via `adapter.py` |
| 9 | Test sync | ✅ | `test_memory_files.py` and `test_memory_integration.py` deleted. New tests in `test_memory_context.py` and updated `test_memory_dynamic.py` |
| 10 | Test coverage | ✅ | MEMORY_DIR path, degraded mode, context injection, limit/filter all tested |
| 11 | Security | ✅ | No injection or path traversal risks. Query is passed as parameter to Mem0, not concatenated |
| 12 | No over-engineering | ✅ | Clean adapter pattern with minimal forwarding. No unnecessary abstractions |
| 13 | No direct SDK calls | ✅ | `from mem0 import Memory` only in `dynamic.py:74`. All callers go through adapter layer |

## Findings

### Finding 1 -- CLAUDE.md still contains file memory references (Important)

**Files**: `/Users/tongliu/work/friday/CLAUDE.md`, lines 11 and 21

**Problem**: Task T010 required removing all "双层记忆" and "文件记忆" descriptions from CLAUDE.md. Two stale references remain:

- Line 11: `- 记忆: Mem0（动态）+ 文件记忆（结构化）`
- Line 21: `└── 记忆系统(Mem0+文件)`

These contradict the updated section on line 91-93 which correctly describes the dynamic-only memory system.

**Suggestion**: Update line 11 to `- 记忆: Mem0（动态记忆）` and line 21 to `└── 记忆系统(Mem0)`.

### Finding 2 -- MemorySearchResult.source docstring references removed functionality (Important)

**File**: `/Users/tongliu/work/friday/src/friday/memory/dynamic.py`, line 31

**Problem**: The `source` field docstring reads `source: str  # "dynamic" / "files"`. Since `files.py` has been deleted and all file memory functionality removed (FR-001, FR-009), the `"files"` value is now dead documentation. It misleadingly suggests the system still has a file memory source, which could confuse future developers.

**Suggestion**: Update the comment to `source: str  # always "dynamic"` or remove the comment entirely since the field is always set to `"dynamic"` in the current codebase. Alternatively, if `source` is kept for forward-compatibility, the comment should reflect that (e.g., `# "dynamic" — extensible for future sources`).

### Finding 3 -- CLAUDE.md has duplicate line (Suggestion)

**File**: `/Users/tongliu/work/friday/CLAUDE.md`, lines 144-145

**Problem**: Line 144 and 145 are identical: `- 工程化数据：\`.specify/\`（spec-kit SDD 工作流）`. This is a copy-paste artifact.

**Suggestion**: Delete the duplicate line 145.

### What was done well

- **Clean deletion**: `files.py`, `test_memory_files.py`, and `test_memory_integration.py` are fully removed with no dangling references in the codebase.
- **Proper adapter simplification**: `adapter.py` is now a clean 32-line forwarding layer with no stale imports.
- **Score threshold filtering**: The `_build_context()` implementation at `repl.py:127` uses `r.score >= 0.3` and `memories[:5]` for both quality and quantity control, directly satisfying FR-005 and FR-006.
- **Graceful degradation**: `_build_context()` wraps everything in try/except (line 129), and `search_memory()` returns empty list when Mem0 is None (line 141-142), satisfying FR-007.
- **Query from user message**: `session.messages[-1].content` is used as the search query (line 122), replacing the hardcoded keywords, satisfying FR-005.
- **MEMORY_DIR correction**: Properly changed to `CONFIG_DIR / "memory"` (line 12 of dynamic.py), placing data at `~/.friday/memory/`, satisfying FR-008.
- **Test coverage**: The new `test_memory_context.py` covers query source, limits, score filtering, and degradation paths. `test_memory_dynamic.py` covers MEMORY_DIR path assertions.
- **Type consistency**: `search_memories()` returns `list[MemorySearchResult]` and `_build_context()` accesses `.score` and `.content` attributes correctly, fixing the prior dict-access mismatch.

## Verdict

CHANGES REQUIRED

Three findings need attention before merge: two stale file memory references in CLAUDE.md (lines 11, 21) and the misleading `source` field docstring in `MemorySearchResult`. These are straightforward text edits. The duplicate line in CLAUDE.md is cosmetic but should also be cleaned up.
