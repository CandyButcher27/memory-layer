---
name: mimi-start
description: Set a project up with mimi, once. Run again later only when you want a brief of where the last session stopped; the memory loads into every session without it.
allowed-tools: Read, Edit, Write, Grep, Glob, Bash
---

# mimi-start

Get the project's memory ready. Follow the steps in order.

## 0. Find the script

- If `mimi/MIMI.md` exists, the script's path is on its `Find rot:` line.
- Otherwise it is `memlayer.py` in the `mimi` skill folder, which sits next to this skill's folder:
  `../mimi/memlayer.py` from the folder holding this file. Common skill folders are `~/.claude/skills`,
  `~/.agents/skills`, `~/.config/opencode/skills`, `~/.gemini/skills`, `~/.gemini/config/skills`, `~/.gemini/antigravity/skills` and `~/.cursor/skills`.
- If the file does not exist, stop and tell the user mimi is not installed.

Call it `$ML` below. Run it with `python`, or `python3` where `python` is missing.

## 1. No `mimi/` folder: set the project up

Follow the mimi skill (`SKILL.md`, next to `$ML`). Pick **New** if the repo has little history and **Adopt**
if it has code, commits or notes. Everything goes in `mimi/`: `init` creates the files, adds
`mimi/.gitignore` so git ignores the folder, and adds one block that loads `mimi/MIMI.md` to each of
`CLAUDE.md`, `AGENTS.md` and `GEMINI.md` that exists, or to a new `CLAUDE.md` and `AGENTS.md` when none
does, which covers Claude Code, Codex, OpenCode, Cursor and Copilot. Do not create any instruction file
yourself. Finish with the skill's report and stop. Do not start other work in the same turn.

## 2. `mimi/` exists: refresh and brief

1. Run `python "$ML" index .`, then `python "$ML" check .`.
   - A stale index is fixed by `index`, which already ran.
   - Do not fix anything else `check` prints. Put it in the brief.
2. `mimi/STATE.md` loads with the instruction file; read it if it is not in your context. Compare its `## Last session` section with the
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
