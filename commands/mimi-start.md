---
description: Start a work session with mimi. Sets up the memory layer if the project has none; otherwise refreshes the index, checks for rot and briefs where the last session stopped.
allowed-tools: Read, Edit, Write, Grep, Glob, Bash
---

# /mimi-start

Get the project's memory ready before work begins. Follow the steps in order.

## 0. Find the script

- If `CLAUDE.md` has a `<!-- memory-layer:start -->` block, the script's path is on its `Find rot:` line.
- Otherwise use `$HOME/.claude/skills/mimi/memlayer.py`.
- If the file does not exist, stop and tell the user mimi is not installed.

Call it `$ML` below.

## 1. No block: set the project up

Follow the mimi skill (`SKILL.md`, next to `$ML`). Pick **New** if the repo has little history and **Adopt**
if it has code, commits or notes. Finish with the skill's report and stop. Do not start other work in the
same turn.

## 2. Block present: refresh and brief

1. Run `python "$ML" index .`, then `python "$ML" check .`.
   - A stale index is fixed by `index`, which already ran.
   - Do not fix anything else `check` prints. Put it in the brief.
2. `STATE.md` is already loaded through `CLAUDE.md`. Compare its `## Last session` section with the
   working tree: `git branch --show-current` and `git status --short`. Note any mismatch, such as a
   different branch or uncommitted files the handoff does not list. Work happened outside a session.
3. Brief the user in at most 10 lines:
   - `Goal:` and anything under `Broken`
   - `Stopped at:`, `Tried, failed:` and `Resume with:` from the handoff
   - mismatches from step 2
   - the `check` result
4. Stop and wait for the task.

Do not open `ISSUES.md`, `decisions.md` or `memory/` files here. A task reads them through the index when
it needs them.
