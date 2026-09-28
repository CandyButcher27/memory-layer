# mimi, the memory layer agent

A project-memory agent for coding agents such as Claude Code. It gives every session a small, trusted
place to look before grepping the repository. It sets that place up on a new project, builds it from
what already exists on an old one, keeps it from rotting, and decides what is worth remembering.

It is a skill (`SKILL.md`), a stdlib-only script (`memlayer.py`) and a set of templates (`templates/`).
It needs no server, no database and no dependencies.

## What it maintains in a project

Everything lives in `mimi/` at the project root. `mimi/.gitignore` (`*`) keeps the folder out of git.
`CLAUDE.md` gets one managed line, `@mimi/MIMI.md`, and `/mimi-logging` reports go to `mimi/logs/`.

| File | Holds | Cap | Updated |
|---|---|---|---|
| `mimi/MIMI.md` | Map: where to look for what, hard rules, the memory index | ~100 lines | When the layout changes |
| `mimi/STATE.md` | Now only: goal, deployed, broken, open threads, next 3, and a `## Last session` handoff (branch, uncommitted, stopped at, tried and failed, resume with) | 60 lines | Overwritten every session |
| `mimi/ISSUES.md` | Every bug: exact symptom, cause, fix commit, test | Append-only | Per bug |
| `mimi/decisions.md` | Choices someone would argue again: why, what was rejected, what reverses it | Short entries | Per decision |
| `mimi/memory/<topic>.md` | Only what the code cannot tell you: external-system quirks, measured numbers with date and sample, traps, non-obvious whys | 150 lines each | When that topic changes |

`CLAUDE.md` imports `mimi/MIMI.md`, which imports `STATE.md`, so each session starts with the map and
the current state already loaded. The index lines in `mimi/MIMI.md` say which file answers which question, and `memlayer.py index`
appends each memory file's `##` headings to its line. That lets a task that names a symptom find the
right file without searching.

## Modes

| Mode | When | What it does |
|---|---|---|
| **New** | Fresh project | `memlayer.py init`, asks for the one-line goal, stops. Memory grows from real events, not guesses |
| **Adopt** | Existing project | `init`, then gathers candidates from the old `CLAUDE.md`, `memory/`, `.harness/`, README, `git log`, issues and deploy config. Keeps only what passes the one-minute test and routes each fact to its file. Reports what moved and what was dropped. Deletes old sources only with approval |
| **Check** | Any time | `memlayer.py check` reports mechanical rot. The agent also looks for duplicates, lines that repeat the code, and headings that name a topic instead of a trap |

## Commands

```bash
python memlayer.py init  [dir]   # create mimi/ and the CLAUDE.md import; never overwrites
python memlayer.py index [dir]   # refresh index lines in mimi/MIMI.md from each memory file's ## headings; idempotent
python memlayer.py check [dir]   # report rot, exit 1 if any
python memlayer.py stats [dir]   # usage and token report from session logs, saved to mimi/logs/
python memlayer.py selftest      # prints SELFTEST_OK
```

`check` flags (all covered by `eval/stress/s1/test_memlayer_stress.py`):
- `mimi/MIMI.md` over 100 lines, or `mimi/STATE.md` over 60
- `CLAUDE.md` + `mimi/MIMI.md` + `mimi/STATE.md` over 16 KB together, since all three load into every
  session
- a `CLAUDE.md` that no longer imports `mimi/MIMI.md`
- a memory file over 150 lines, or in a subfolder of `mimi/memory/` (allowed, but noted)
- a memory file missing from the index, an index line pointing to a missing file, or index lines
  gone stale since the headings changed
- a `Last verified:` date that is missing, malformed, in the future, duplicated, or more than 90
  days old
- a `## ISS-` issue entry without `Symptom:` or `Cause:` (code blocks inside an entry are ignored)
- git conflict markers in any layer file

The script keeps each file's own line endings, and only touches `CLAUDE.md` to add its one managed
import. It writes its own path as `$HOME/...`, so the map works on any machine. Errors are reported as one line, never
as a traceback.

## Slash commands

| Command | When | What it does |
|---|---|---|
| `/mimi-start` | Once per project | Sets the project up (New or Adopt) if it has no `mimi/`. Run again later only for a brief: it runs `index` and `check`, compares the `Last session` handoff with the working tree, and says where work stopped |
| `/mimi-close` | End of a session | Writes what the session learned, rewrites `mimi/STATE.md`, runs `index` and `check` (below) |
| `/mimi-logging` | Any time | Runs `stats`, saves the report to `mimi/logs/`, and reads the result: tokens loaded per session, per-prompt tokens and searches before and after adoption, memory files never read |

## Closing a session: `/mimi-close`

`commands/mimi-close.md` is a slash command to run at the end of every work session. It:

1. Stops if the project has no `mimi/MIMI.md`. It never creates the files itself.
2. Gathers candidates from the conversation, git status and diff, this session's commits, and the
   memory files the work touched.
3. Drops anything the code or git already shows, plus narration and descriptions of how the code
   works. Scope is never a reason to drop: a fact about the user's own systems is kept.
4. Routes each surviving fact to exactly one place:
   - a bug → `mimi/ISSUES.md`
   - a choice → `mimi/decisions.md`
   - a correction → edited in place everywhere the old value appears
   - an external fact, measurement or trap → `mimi/memory/<topic>.md`, under a heading named after the
     trap
5. Runs `index` before writing the state.
6. Rewrites `mimi/STATE.md` to show only what is true now, including the `## Last session` handoff.
   - Its `Tried, failed:` line keeps dead ends the user mentioned from being retried.
   - It points to facts already in `mimi/memory/` instead of repeating them.
   - Then it runs `check` until clean.
7. Verifies that no fact is duplicated and no corrected value survives as current.
8. Reports what was written, corrected and dropped, the open questions and the `check` result. It
   does not commit unless asked.

Tested on a scratch copy of the production project:
- A new external fact got its own trap-named heading.
- A corrected cost figure was replaced everywhere it appeared, while a dated decision record kept the
  old figure on purpose.
- Numbers with no source became questions.
- `check` was clean, and nothing was committed.
- A second run with nothing new wrote nothing.
- One close cost about $0.70.

To install it, copy `commands/mimi-*.md` to `~/.claude/commands/`. In Git Bash, `claude -p
"/mimi-close"` gets the leading `/` rewritten into a Windows path. Type the command inside Claude
Code instead, or set `MSYS_NO_PATHCONV=1`.

## Rules the agent follows

- **Write only what the code cannot tell you.** The test for every line: could someone learn this in
  under a minute from the code or a command? If yes, don't write it.
- **Every fact needs something checkable behind it:** a commit, an issue ID, a command, or a date with
  sample size.
- **A wrong line gets fixed or deleted, never a correct one added beside it.**
- **A code change alone writes nothing.** Git has it.
- **Each trap gets its own `##` heading**, named the way a task would describe it (error text, library,
  table, command). After every memory edit, run `index`, then `check` until clean.
- **Apply the one-minute test to each fact on its own.** A number, date, decision or constraint that a
  person stated is never in the code.
- **A memory miss is not an answer.** Files marked `— empty` are skipped. When memory has nothing,
  fall back to `git log --grep` and the code.
- **Split `memory/` by external boundary or subsystem**, not by code folder, and only after a real miss.
- **Never overwrite prose a user wrote.** Never delete old memory sources without approval.

## How it was evaluated

The full method and results are in `docs/EVALUATION.md`. It ran on one real project (a private project, 171
commits), comparing no memory, the current `.harness/` + `memory/` setup, and this layer.

| Metric | What it measures |
|---|---|
| Accuracy | Fraction of answer-key points a blind Sonnet judge finds in the answer. Keys come from commits, code, or facts given in the task, never from either memory system |
| Wrong claims | Claims the judge marks false or contradicting the key |
| Tool calls, search calls | How much the agent had to dig, where search calls are Grep and Glob |
| Input tokens, cost, time | What each answer cost to produce |
| Memory lines written | Growth of the memory after the same work sessions |
| Files per fact | Duplication: in how many files each fact was written |
| Correction handling | Whether a corrected fact was edited in place or left beside the old one |
| Restraint | Whether a session with nothing durable in it wrote memory anyway |

**Headline results:**

| | Current setup | This layer |
|---|---|---|
| Retrieval accuracy (12 past-incident tasks × 2) | 0.93 | 0.93 (0.88 before `index` existed) |
| Memory size after adopting the same project | ~4,600 lines | 744 lines |
| Memory lines written in 6 identical sessions | +208 | +83 |
| Recall accuracy of facts learned in those sessions | 0.97 | 0.97 |
| Per recall answer: tool calls / searches / cost | 4.4 / 2.6 / $0.08 | 3.0 / 1.1 / $0.06 |
| Wrong claims per recall answer | 0.20 | 0.07 |

Handoff test (3 runs per arm): with or without the `## Last session` section, every run resumed the
right task at the right step. With the section, the dead end the user had mentioned was written into
`STATE.md` 3 of 3 times. Without it, 1 of 3, and one run went on to reopen that closed choice.

**Five large public repos** (git, django, cargo, node, go; details in `docs/EVALUATION.md`, Experiment 7):

| | No memory | Current setup | This layer |
|---|---|---|---|
| Retrieval of past incidents, mean | 0.81 | 0.81 | 0.76 |
| Recall of facts people stated, mean | – | 0.29 | **0.79** (won on all 5) |
| Recall cost per answer | – | $0.07 | $0.03 |

It is much better at keeping what people tell it. It is slightly worse at finding past incidents on repos
whose commit history already explains them. Experiment 7 lists the four fixes for that. They are now
applied but not yet re-evaluated.

**Stage 1, against Claude Code's built-in auto-memory and claude-mem** (cargo and sqlite-utils,
pre-registered in `eval/stage1/PREREG.md`; results in `eval/stage1/RESULTS.md`):

| | No memory | Auto-memory | claude-mem | mimi |
|---|---|---|---|---|
| Facts mentioned in passing, accuracy (48 answers) | 0.09 | 0.51 | 0.15 | **0.83** |
| Resuming unfinished work, accuracy (20 answers) | 0.39 | 0.80 | 0.42 | **0.97** |
| Cost per answer | $0.06–0.07 | $0.04 | $0.08–0.09 | **$0.03** |

- Every pre-registered rule for a mimi win was met. The continuity lead over auto-memory rests on 4
  questions, with a lower bound of +0.02.
- `/mimi-close` dropped two person-stated facts as "about your downstream service". Commit `3bdb281`
  makes scope never a reason to drop.
- A re-run of that repo and 8 more continuity questions are pre-registered in
  `eval/stage1/PREREG-2.md`. **Neither has run yet.**

## Status

Installed as a user-level skill on 2026-09-28:
- the skill in `~/.claude/skills/mimi/`
- the commands in `~/.claude/commands/`

It is not the default: `/harness` and `/wrapup` still build the old setup. Switching fully means pointing
`/harness` and `/wrapup` at mimi, then running `/mimi-start` (Adopt) project by project.
