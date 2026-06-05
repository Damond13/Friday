---
description: Execute the implementation plan by processing and executing all tasks defined in tasks.md
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Role Assignment: Developer

**You are operating as the Developer Agent.** Load and follow `.claude/agents/developer.md` as your role constraints:

- Only write code according to `tasks.md` order — no extra features
- Do not modify code outside the plan scope
- Do not auto-commit/push — wait for explicit user instruction
- Report ambiguities to `specs/*/review.md` "Questions" section, do not guess
- All LLM calls must go through `llm/adapter.py`, no direct API calls
- All data operations must go through the corresponding module's storage layer

**After implementation completes, suggest running `/speckit.review` for code review.**

## Pre-Execution Checks

**Check for extension hooks (before implementation)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_implement` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Pre-Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```
  - **Mandatory hook** (`optional: false`):
    ```
    ## Extension Hooks

    **Automatic Pre-Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}
    
    Wait for the result of the hook command before proceeding to the Outline.
    ```
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently

## Outline

1. Run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Check checklists status** (if FEATURE_DIR/checklists/ exists):
   - Scan all checklist files in the checklists/ directory
   - For each checklist, count:
     - Total items: All lines matching `- [ ]` or `- [X]` or `- [x]`
     - Completed items: Lines matching `- [X]` or `- [x]`
     - Incomplete items: Lines matching `- [ ]`
   - Create a status table:

     ```text
     | Checklist | Total | Completed | Incomplete | Status |
     |-----------|-------|-----------|------------|--------|
     | ux.md     | 12    | 12        | 0          | ✓ PASS |
     | test.md   | 8     | 5         | 3          | ✗ FAIL |
     | security.md | 6   | 6         | 0          | ✓ PASS |
     ```

   - Calculate overall status:
     - **PASS**: All checklists have 0 incomplete items
     - **FAIL**: One or more checklists have incomplete items

   - **If any checklist is incomplete**:
     - Display the table with incomplete item counts
     - **STOP** and ask: "Some checklists are incomplete. Do you want to proceed with implementation anyway? (yes/no)"
     - Wait for user response before continuing
     - If user says "no" or "wait" or "stop", halt execution
     - If user says "yes" or "proceed" or "continue", proceed to step 3

   - **If all checklists are complete**:
     - Display the table showing all checklists passed
     - Automatically proceed to step 3

3. Load and analyze the implementation context:
   - **REQUIRED**: Read tasks.md for the complete task list and execution plan
   - **REQUIRED**: Read plan.md for tech stack, architecture, and file structure
   - **IF EXISTS**: Read data-model.md for entities and relationships
   - **IF EXISTS**: Read contracts/ for API specifications and test requirements
   - **IF EXISTS**: Read research.md for technical decisions and constraints
   - **IF EXISTS**: Read .specify/memory/constitution.md for governance constraints
   - **IF EXISTS**: Read quickstart.md for integration scenarios

4. **Project Setup Verification**:
   - **REQUIRED**: Create/verify ignore files based on actual project setup:

   **Detection & Creation Logic**:
   - Check if the following command succeeds to determine if the repository is a git repo (create/verify .gitignore if so):

     ```sh
     git rev-parse --git-dir 2>/dev/null
     ```

   - Check if Dockerfile* exists or Docker in plan.md → create/verify .dockerignore
   - Check if .eslintrc* exists → create/verify .eslintignore
   - Check if eslint.config.* exists → ensure the config's `ignores` entries cover required patterns
   - Check if .prettierrc* exists → create/verify .prettierignore
   - Check if .npmrc or package.json exists → create/verify .npmignore (if publishing)
   - Check if terraform files (*.tf) exist → create/verify .terraformignore
   - Check if .helmignore needed (helm charts present) → create/verify .helmignore

   **If ignore file already exists**: Verify it contains essential patterns, append missing critical patterns only
   **If ignore file missing**: Create with full pattern set for detected technology

   **Common Patterns by Technology** (from plan.md tech stack):
   - **Node.js/JavaScript/TypeScript**: `node_modules/`, `dist/`, `build/`, `*.log`, `.env*`
   - **Python**: `__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `dist/`, `*.egg-info/`
   - **Java**: `target/`, `*.class`, `*.jar`, `.gradle/`, `build/`
   - **C#/.NET**: `bin/`, `obj/`, `*.user`, `*.suo`, `packages/`
   - **Go**: `*.exe`, `*.test`, `vendor/`, `*.out`
   - **Ruby**: `.bundle/`, `log/`, `tmp/`, `*.gem`, `vendor/bundle/`
   - **PHP**: `vendor/`, `*.log`, `*.cache`, `*.env`
   - **Rust**: `target/`, `debug/`, `release/`, `*.rs.bk`, `*.rlib`, `*.prof*`, `.idea/`, `*.log`, `.env*`
   - **Kotlin**: `build/`, `out/`, `.gradle/`, `.idea/`, `*.class`, `*.jar`, `*.iml`, `*.log`, `.env*`
   - **C++**: `build/`, `bin/`, `obj/`, `out/`, `*.o`, `*.so`, `*.a`, `*.exe`, `*.dll`, `.idea/`, `*.log`, `.env*`
   - **C**: `build/`, `bin/`, `obj/`, `out/`, `*.o`, `*.a`, `*.so`, `*.exe`, `*.dll`, `autom4te.cache/`, `config.status`, `config.log`, `.idea/`, `*.log`, `.env*`
   - **Swift**: `.build/`, `DerivedData/`, `*.swiftpm/`, `Packages/`
   - **R**: `.Rproj.user/`, `.Rhistory`, `.RData`, `.Ruserdata`, `*.Rproj`, `packrat/`, `renv/`
   - **Universal**: `.DS_Store`, `Thumbs.db`, `*.tmp`, `*.swp`, `.vscode/`, `.idea/`

   **Tool-Specific Patterns**:
   - **Docker**: `node_modules/`, `.git/`, `Dockerfile*`, `.dockerignore`, `*.log*`, `.env*`, `coverage/`
   - **ESLint**: `node_modules/`, `dist/`, `build/`, `coverage/`, `*.min.js`
   - **Prettier**: `node_modules/`, `dist/`, `build/`, `coverage/`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`
   - **Terraform**: `.terraform/`, `*.tfstate*`, `*.tfvars`, `.terraform.lock.hcl`
   - **Kubernetes/k8s**: `*.secret.yaml`, `secrets/`, `.kube/`, `kubeconfig*`, `*.key`, `*.crt`

5. Parse tasks.md and detect execution mode:

   **Scan for `## Parallel Groups` section** in tasks.md:
   - If found: extract the group table → **Orchestrator Mode** (proceed to step 6)
   - If NOT found: fall back to scanning for `[P]` markers → **Legacy Mode** (proceed to step 8)
   - If user input contains `--no-parallel` or `no-parallel`: force **Legacy Mode** regardless

6. **Orchestrator Mode** — Group-based parallel execution:

   Process groups in order (G0 → G1 → G2 → ...). For each group:

   **a) Single-task group (1 task)**: Execute directly in the main Agent session (no worktree needed). Apply the Developer Agent constraints. Mark task `[X]` in tasks.md when done.

   **b) Multi-task group (2+ tasks)**: Dispatch parallel sub-Agents:
   - For each task in the group, launch an `Agent` tool call with:
     - `isolation: "worktree"` — Claude Code handles worktree creation/merge/cleanup
     - `description`: "{TaskID}: {short description}"
     - `prompt`: Constructed per step 7 below
   - Issue ALL Agent calls for the group in a **single message** (this triggers concurrent execution)
   - **Concurrency control**: If `max_concurrency` is set in the Parallel Groups table, limit concurrent Agents to that number by batching (e.g., max_concurrency=2 with 5 tasks → 3 batches)
   - **force_sequential override**: If a task has `force_sequential` in its description, remove it from the parallel batch and execute it in the main session after the group's parallel tasks complete
   - Wait for ALL agents in the group to complete before proceeding to the next group
   - After group completion, report results and mark tasks `[X]` in tasks.md

   **c) Group failure handling**:
   - If ANY sub-agent in a group fails: pause execution, report which task(s) failed and the error details
   - Do NOT proceed to the next group until the user decides: retry, skip, or abort
   - If user says "skip": mark the failed task with a note in tasks.md, proceed to next group
   - If user says "abort": stop execution entirely

7. **Sub-Agent context preparation**:

   For each parallel task dispatched to a sub-Agent, construct a minimal but sufficient prompt:

   ```
   You are implementing task {TaskID} for the {feature name} feature.

   ## Your Task
   {Full task description from tasks.md}

   ## Context
   - Feature: {feature name from spec.md}
   - Target files: {file paths from task description}
   - Tech stack: {from plan.md Technical Context}

   ## Relevant Design
   {Extract from plan.md: only sections directly related to this task's files/concepts}

   ## Relevant Contracts (if applicable)
   {Extract from contracts/: only items related to this task's interfaces}

   ## Coding Standards
   - Follow Developer Agent constraints from .claude/agents/developer.md
   - Max 30 lines per function, 200 lines per file (for code files)
   - All external calls through adapter layer
   - Type annotations required

   ## After Implementation
   Report what you changed and which files were created/modified.
   ```

   **Key principle**: Include only what the sub-Agent needs — task description, relevant design excerpt, target files. Do NOT send the full spec, full plan, or unrelated contracts.

8. **Legacy Mode** — Serial execution (backward compatible):

   When tasks.md has no `## Parallel Groups` section or user requested `--no-parallel`:

   - Parse tasks by phase (Setup, Foundational, User Stories, Polish)
   - Execute tasks sequentially in phase order
   - Tasks with `[P]` markers are noted but executed one at a time
   - Mark each completed task `[X]` in tasks.md
   - This mode produces identical behavior to the pre-parallel implement command

9. Progress tracking and completion:

   - **Orchestrator Mode**: Report after each group completes (tasks done, tasks remaining, next group)
   - **Legacy Mode**: Report after each task completes
   - **IMPORTANT**: Mark completed tasks as `[X]` in tasks.md immediately after each task/group finishes
   - After all tasks complete:
     - Verify all tasks marked `[X]`
     - Check implementation matches specification
     - Confirm coding standards followed

## Mandatory Post-Execution Hooks

**You MUST complete this section before reporting completion to the user.**

Check if `.specify/extensions.yml` exists in the project root.
- If it does not exist, or no hooks are registered under `hooks.after_implement`, skip to the Completion Report.
- If it exists, read it and look for entries under the `hooks.after_implement` key.
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue to the Completion Report.
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- For each executable hook, output the following based on its `optional` flag:
  - **Mandatory hook** (`optional: false`) — **You MUST emit `EXECUTE_COMMAND:` for each mandatory hook**:
    ```
    ## Extension Hooks

    **Automatic Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}
    ```
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```

## Completion Report

Report final status with summary of completed work:
- Execution mode used: Orchestrator Mode (parallel) or Legacy Mode (serial)
- Tasks completed vs total
- Groups processed (if Orchestrator Mode)
- Any failed or skipped tasks
- Files modified

## Done When

- [ ] All tasks in tasks.md completed and marked `[X]`
- [ ] Implementation validated against specification, plan, and test coverage
- [ ] Extension hooks dispatched or skipped according to the rules in Mandatory Post-Execution Hooks above
- [ ] Completion reported to user with execution mode, task summary, and files modified

## Strategy Controls

The following controls allow developers to adjust parallel execution behavior:

### In tasks.md Parallel Groups Table

| Control | Where | Effect |
|---------|-------|--------|
| `max_concurrency` | Parallel Groups table `**Max parallelism**` line | Limit concurrent sub-Agents per group |
| `force_sequential` | Individual task description | Remove task from parallel batch, execute serially |

### In user prompt (when running `/speckit.implement`)

| Instruction | Effect |
|-------------|--------|
| `--no-parallel` or `no-parallel` | Force full serial execution (Legacy Mode) |
| (no instruction) | Use groups from tasks.md (Orchestrator Mode), or Legacy if no groups |

### Backward Compatibility

- tasks.md without `## Parallel Groups` section → Legacy Mode (identical to pre-parallel behavior)
- tasks.md without `[G{n}]` markers on tasks → all tasks treated as G0 (serial)
- `--no-parallel` always available as escape hatch
