---
name: memory-layer
description: Set up, adopt, or audit a project's memory layer (CLAUDE.md map, STATE.md, ISSUES.md, decisions.md, memory/<topic>.md) so the agent checks memory before grepping the repo. Use when the user says "/memory-layer", "set up memory", "add the memory layer to this project", "adopt memory layer", "check memory for rot", or starts a new project.
---

# memory-layer

Five kinds of file, one of each:

| File | Holds | Cap | Updated |
|---|---|---|---|
| `CLAUDE.md` | Map: where things are, which file to read for what, hard rules | ~100 lines | When the layout changes |
| `STATE.md` | Now only: goal, deployed commit, broken, open threads, next 3, `## Last session` handoff | 60 lines | Overwritten every session |
| `ISSUES.md` | Every bug: exact symptom, cause, fix commit, test | None, append-only | Per bug |
| `decisions.md` | Choices someone would argue again: why, what reverses it | Short entries | Per decision |
| `memory/<topic>.md` | What the code cannot tell you | 150 lines each | When that topic changes |

`CLAUDE.md` imports `STATE.md` with `@STATE.md`, so every session starts with the current state
already loaded and an index saying which file answers which question. That index is what replaces
grepping.

`memlayer.py` sits next to this file. `init` creates missing files and appends a managed block to
`CLAUDE.md` between `<!-- memory-layer:start -->` markers. It never overwrites anything, so it is
safe on any project, any number of times. `check` reports rot and exits 1 when it finds any.

Pick the mode:

- No `<!-- memory-layer:start -->` in `CLAUDE.md` and the repo has little history → **New**
- No marker, but the repo has code, commits, or notes → **Adopt**
- Marker present → **Check**

## Index lines

The index in `CLAUDE.md` is the only thing that makes a memory file get read. An agent matches its
task against these lines, and a task names its symptom, not its topic. A hand-written line drifts
toward the topic, so the symptom words come from the file itself:

- Each trap in a memory file gets its own `##` heading, named the way a task would describe it:
  `## Stripe sends the same webhook event twice`, not `## Webhooks`.
- `python memlayer.py index <project>` appends every file's headings to its index line as
  `— contains: …`. Run it after any memory edit. It is idempotent.

## New

1. `python memlayer.py init <project>`
2. Ask the user for the one-line goal if the repo does not make it plain. Write it into `STATE.md`.
3. Stop there. Memory grows from real bugs, decisions and external facts, not from a guess on day one.

## Adopt (existing project)

1. `python memlayer.py init <project>`.
2. Gather candidates. Read, don't edit:
   - existing `CLAUDE.md`, `README*`, `TODO*`, `NOTES*`, any `memory/`, `.harness/`, `docs/`
   - `git log --oneline -200`, especially `fix:` commits and reverts
   - `gh issue list --state all --limit 50` if a GitHub remote exists
   - config and deploy files (`Dockerfile`, CI workflows, `.env.example`, `railway.json` and the like) for external systems
3. Route each candidate through this test: could someone learn it in under a minute by reading the
   code or running a command? If yes, drop it. If no:
   - bug with a known symptom → `ISSUES.md`, citing the fix commit
   - deliberate choice with a reason → `decisions.md`
   - external quirk, measured number, trap, non-obvious "why" → `memory/<topic>.md`, plus an index line in the `CLAUDE.md` block (see *Index lines*)
   - what is in flight now → `STATE.md`
   - finished work, session narration, descriptions of how the code works → drop
4. Every written fact cites something checkable: commit, issue ID, command, or date with sample size.
   A claim with nothing behind it goes to the user as a question, not into a file.
5. Do not delete or rewrite the old sources. Report to the user: what moved where, what was dropped
   and why, which old files now look redundant. Delete only what the user approves.
6. Run `index`, then `check` until it prints `memory layer clean`.

## Check

Run `python memlayer.py check <project>` and fix each line it prints:

- over cap → trim. `STATE.md` over cap usually means finished work was never removed.
- not in the index → add a "read when" line, or merge the file into another and delete it.
- stale `Last verified:` → re-check each fact against reality. Fix it or delete it, then bump the date.

The script cannot see these. Look for them yourself:

- a heading that names a topic, not a trap (`## Webhooks`) → rename it after the trap, or split
  the section so each trap has its own heading. Then run `index`.
- two files answering the same question → merge
- a line that repeats the code → delete
- a `memory/` file nobody has needed in a month of sessions → merge or delete
