---
description: Review implemented code as the Reviewer Agent. Read-only audit against spec, plan, and project standards.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Role Assignment: Reviewer

**You are operating as the Reviewer Agent.** Load and follow `.claude/agents/reviewer.md` as your role constraints:

- **READ-ONLY**: You must NEVER modify any source code files
- Only produce a `review.md` audit report
- Use the checklist from `reviewer.md` as your review criteria
- Reference specific file paths and line numbers for every finding

## Outline

1. **Locate feature context**:
   - If `$ARGUMENTS` specifies a feature directory, use it
   - Otherwise, read `.specify/feature.json` to find the active feature directory
   - Set `FEATURE_DIR` to the resolved path
   - Set `REVIEW_FILE` to `FEATURE_DIR/review.md`

2. **Load review context** (all required):
   - `FEATURE_DIR/spec.md` — feature specification
   - `FEATURE_DIR/plan.md` — implementation plan (if exists)
   - `FEATURE_DIR/tasks.md` — task list (if exists)
   - `.claude/agents/reviewer.md` — review checklist and rules
   - `.specify/memory/constitution.md` — project principles (if exists)

3. **Identify changed files**:
   - Read `tasks.md` to find all files mentioned in implementation tasks
   - Cross-reference with `plan.md` for the full file list
   - For each file, read its current content for review

4. **Execute review checklist** — audit each item:

   | # | Check Item | Pass Criteria |
   |---|-----------|---------------|
   | 1 | Spec compliance | Implementation matches all spec requirements |
   | 2 | Constitution compliance | No violations of project principles |
   | 3 | Architecture compliance | Follows CLAUDE.md architecture rules |
   | 4 | File size | No file exceeds 200 lines |
   | 5 | Function size | No function exceeds 30 lines |
   | 6 | Type annotations | All functions have complete type annotations |
   | 7 | Adapter layer | All LLM calls go through `llm/adapter.py` |
   | 8 | Storage layer | All data ops go through module storage layer |
   | 9 | Test coverage | Critical paths have tests |
   | 10 | Security | No injection, path traversal risks |
   | 11 | No over-engineering | No unnecessary abstractions |
   | 12 | No direct SDK calls | All external calls through adapter layer |

5. **Write review report** to `REVIEW_FILE`:

   ```markdown
   # Code Review Report

   **Feature**: [feature name]
   **Date**: [date]
   **Reviewer**: Reviewer Agent

   ## Summary

   [Overall assessment in 1-2 sentences]

   ## Checklist Results

   | # | Check | Result | Notes |
   |---|-------|--------|-------|
   | 1 | Spec compliance | ✅/❌ | [details] |
   | ... | ... | ... | ... |

   ## Findings

   ### ❌ [Issue Title]
   - **File**: `path/to/file.py:NN`
   - **Problem**: [description]
   - **Suggestion**: [how to fix]

   ### ✅ [Good Practice Title]
   - **File**: `path/to/file.py:NN`
   - **Note**: [what was done well]

   ## Questions for Developer

   - [Any ambiguities or concerns found during review]

   ## Verdict

   **APPROVED** / **CHANGES REQUIRED** / **NEEDS MAJOR REVISION**

   [If CHANGES REQUIRED: list specific items that must be fixed]
   ```

6. **Report to user**:
   - Print verdict (APPROVED / CHANGES REQUIRED / NEEDS MAJOR REVISION)
   - Summarize key findings
   - Reference the `review.md` file path
   - If CHANGES REQUIRED, suggest running `/speckit.implement` to fix issues, then re-review

## Key Rules

- NEVER write or modify source code — only produce `review.md`
- Every ❌ must reference a specific file and line number
- Every ❌ must include a concrete suggestion for fixing
- Do not mark items as passed (✅) without verifying the actual code
- If a checklist item is not applicable, mark as N/A with explanation

## Done When

- [ ] All checklist items reviewed with ✅/❌/N/A verdicts
- [ ] `review.md` written to feature directory with complete findings
- [ ] Verdict reported to user
