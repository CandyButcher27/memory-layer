---
description: Set a project up with mimi, once. Run again later only when you want a brief of where the last session stopped; the memory loads into every session without it.
allowed-tools: Read, Edit, Write, Grep, Glob, Bash
---

# /mimi-start

Get the project's memory ready. Follow the steps in order.

## 0. Find the script

- If `mimi/MIMI.md` exists, the script's path is on its `Find rot:` line.
- Otherwise use `$HOME/.claude/skills/mimi/memlayer.py`.
- If the file does not exist, stop and tell the user mimi is not installed.

Call it `$ML` below.

## 1. No `mimi/` folder: set the project up

Follow the mimi skill (`SKILL.md`, next to `$ML`). Pick **New** if the repo has little history and **Adopt**
if it has code, commits or notes. Everything goes in `mimi/`: `init` creates the files, adds
`mimi/.gitignore` so git ignores the folder, and adds one `@mimi/MIMI.md` import to `CLAUDE.md`. Finish
with the skill's report and stop. Do not start other work in the same turn.

## 2. `mimi/` exists: refresh and brief

1. Run `python "$ML" index .`, then `python "$ML" check .`.
   - A stale index is fixed by `index`, which already ran.
   - Do not fix anything else `check` prints. Put it in the brief.
2. `mimi/STATE.md` is already loaded through `CLAUDE.md`. Compare its `## Last session` section with the
   working tree: `git branch --show-current` and `git status --short`. Note any mismatch, such as a
   different branch or uncommitted files the handoff does not list. That means work happened outside a
   session.
3. Brief the user in at most 10 lines:
   - `Goal:` and anything under `Broken`
   - `Stopped at:`, `Tried, failed:` and `Resume with:` from the handoff
   - mismatches from step 2
   - the `check` result
4. Stop and wait for the task.

Do not open `mimi/ISSUES.md`, `mimi/decisions.md` or `mimi/memory/` files here. A task reads them through
the index when it needs them.
