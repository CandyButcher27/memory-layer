---
name: mimi
description: Set up, adopt, or audit a project's mimi memory (the mimi/ folder - MIMI.md map, STATE.md, ISSUES.md, decisions.md, memory/<topic>.md - loaded from CLAUDE.md, AGENTS.md or GEMINI.md) so the agent checks memory before grepping the repo. Use when the user says "/mimi", "mimi", "set up memory", "add the memory layer to this project", "adopt memory layer", "check memory for rot", or starts a new project.
---

# mimi

Everything mimi keeps lives in one folder, `mimi/`, at the project root. It has five kinds of file,
one of each:

| File | Holds | Cap | Updated |
|---|---|---|---|
| `mimi/MIMI.md` | Map: which file to read for what, hard rules, the memory index | ~100 lines | When the layout changes |
| `mimi/STATE.md` | Now only: goal, deployed commit, broken, open threads, next 3, `## Last session` handoff | 60 lines | Overwritten every session |
| `mimi/ISSUES.md` | Every bug: exact symptom, cause, fix commit, test | None, append-only | Per bug |
| `mimi/decisions.md` | Choices someone would argue again: why, what reverses it | Short entries | Per decision |
| `mimi/memory/<topic>.md` | What the code cannot tell you | 150 lines each | When that topic changes |

`mimi/logs/` holds the reports the `mimi-logging` skill saves.

**How it loads.** Each agent instruction file the project has (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`;
a new `CLAUDE.md` if none) gets one managed block between `<!-- memory-layer:start -->` markers. The block
holds `@mimi/MIMI.md`, which Claude Code and Gemini CLI expand, and a plain line telling any other agent
to read `mimi/MIMI.md` and `mimi/STATE.md`. `MIMI.md` imports `STATE.md`. So every session starts with the
map and the current state already loaded, and an index saying which file answers which question. That
index is what replaces grepping.

**Git.** `mimi/.gitignore` contains `*`, so git ignores the whole folder and the project's own
`.gitignore` is never touched. Memory stays on this machine. Deleting `mimi/.gitignore` shares it through
git.

**Search.** Most agents search with ripgrep, which skips git-ignored files, so it would not search
`mimi/`. `mimi/.ignore` contains `!*`, which ripgrep reads and git does not, so search sees the folder
again. `check` flags the file if it goes missing.

**The script.** `memlayer.py` sits next to this file. Run it with `python`, or `python3` where `python`
is missing.
- `init` creates missing files and the import. It never overwrites anything, so it is safe on any
  project, any number of times.
- `index` refreshes the index lines in `mimi/MIMI.md`.
- `check` reports rot and exits 1 when it finds any:
  - files over their line cap
  - more than 16 KB auto-loaded (instruction file + `MIMI.md` + `STATE.md`)
  - an instruction file that lost the import
  - a stale or broken index
  - missing or bad `Last verified:` dates
  - incomplete `## ISS-` entries
  - git conflict markers
  
  Memory files may sit in subfolders of `mimi/memory/`, but a flat folder is easier to scan, so `check`
  notes them.

Pick the mode:

- No `mimi/MIMI.md` and the repo has little history → **New**
- No `mimi/MIMI.md`, but the repo has code, commits, or notes → **Adopt**
- `mimi/MIMI.md` present → **Check**

## Index lines

The index in `mimi/MIMI.md` is the only thing that makes a memory file get read. An agent matches its
task against these lines, and a task names its symptom, not its topic. A hand-written line drifts toward
the topic, so the symptom words come from the file itself:

- Each trap in a memory file gets its own `##` heading, named the way a task would describe it:
  `## Stripe sends the same webhook event twice`, not `## Webhooks`.
- `python memlayer.py index <project>` appends the headings of every memory file and of `mimi/decisions.md`
  to its index line as `— contains: …`. `mimi/ISSUES.md` is append-only and found by its symptom text, so
  its line gets no headings. It marks a memory file, `mimi/ISSUES.md` or `mimi/decisions.md` that holds nothing
  yet as `— empty`, so a task skips it. Run it after any memory edit, then `check`. It is idempotent.
- The map tells the agent that a memory miss is not an answer: with nothing recorded, it falls back to
  `git log --grep` and the code. A thin memory must never read as "no known issue".

## New

1. `python memlayer.py init <project>`
2. Ask the user for the one-line goal if the repo does not make it plain. Write it into `mimi/STATE.md`.
3. Stop there. Memory grows from real bugs, decisions and external facts, not from a guess on day one.

## Adopt (existing project)

1. `python memlayer.py init <project>`.
2. Gather candidates. Read, don't edit:
   - existing `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `README*`, `TODO*`, `NOTES*`, any old `memory/`, `.harness/`, `docs/`
   - `git log --oneline -200`, especially `fix:` commits and reverts
   - `gh issue list --state all --limit 50` if a GitHub remote exists
   - config and deploy files (`Dockerfile`, CI workflows, `.env.example`, `railway.json` and the like) for external systems
3. Route each candidate through this test: could someone learn it in under a minute by reading the code
   or running a command? If yes, drop it. Apply it to each fact on its own. A number, date, decision or
   constraint a person stated is never "in the code", and scope is never a reason to drop. If no:
   - bug with a known symptom → `mimi/ISSUES.md`, citing the fix commit
   - deliberate choice with a reason → `mimi/decisions.md`
   - external quirk, measured number, trap, non-obvious "why" → `mimi/memory/<topic>.md`, plus an index
     line in `mimi/MIMI.md` (see *Index lines*)
   - what is in flight now → `mimi/STATE.md`
   - finished work, session narration, descriptions of how the code works → drop
4. Every written fact cites something checkable: commit, issue ID, command, or date with sample size.
   A claim with nothing behind it goes to the user as a question, not into a file.
   - `Last verified:` is the date a fact was last checked, not the date it was copied. Keep the source's
     date, or write today only for facts you re-checked in this run.
   - A quirk of the machine you are running on (a temp directory, a tool missing from this shell) is not
     a project fact. Record it only if it holds for everyone who works on the project.
5. Do not delete or rewrite the old sources. Report to the user: what moved where, what was dropped and
   why, and which old files now look redundant.
   - Delete only what the user approves, and only files whose sole purpose is agent memory: the old
     instruction-file content (rewritten, not deleted), an old `memory/`, `.harness/`, and notes addressed to
     the agent (`AGENT_NOTES.md` and the like).
   - Project documentation is never deleted or edited, even when its facts moved into memory: `README*`,
     `CONTRIBUTING*`, `docs/`, `.docs/`, design specs, plans, task lists and anything a person reads.
6. Run `index`, then `check` until it prints `memory layer clean`.
7. Tell the user that `mimi/` is ignored by git through `mimi/.gitignore`, and that deleting that file
   shares the memory with the team. Do not change the project's own `.gitignore`.

## Check

Run `python memlayer.py check <project>` and fix each line it prints:

- over cap → trim. `mimi/STATE.md` over cap usually means finished work was never removed.
- not in the index → add a "read when" line, or merge the file into another and delete it.
- stale `Last verified:` → re-check each fact against reality. Fix it or delete it, then bump the date.
- an instruction file does not import `mimi/MIMI.md` → run `init`, which adds the import back. If the file is
  a project document that only shares the name, such as a product's own `AGENTS.md`, put
  `<!-- memory-layer:skip -->` in it instead: `check` and `init` then leave it alone.

The script cannot see these. Look for them yourself:

- a heading that names a topic, not a trap (`## Webhooks`) → rename it after the trap, or split the
  section so each trap has its own heading. Then run `index`.
- two files answering the same question → merge
- a line that repeats the code → delete
- a `mimi/memory/` file nobody has needed in a month of sessions → merge or delete
