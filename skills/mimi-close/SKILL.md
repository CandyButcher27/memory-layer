---
name: mimi-close
description: Close a work session by writing what this session learned into the project's mimi/ folder (ISSUES, decisions, memory/, STATE), then index and check it.
allowed-tools: Read, Edit, Write, Grep, Glob, Bash
---

# /mimi-close

Bring the project's memory up to date with this session before it ends. Follow every step in order.
Write only what this session actually produced. Never write something because a file has an empty
section.

## 0. Preconditions

- If `mimi/MIMI.md` does not exist, stop and tell the user to set the project up first with
  `/mimi-start`. Do not create files here.
- Find `memlayer.py`: its path is on the `Find rot:` line of `mimi/MIMI.md`. Call it `$ML` below.
- Every memory file lives in `mimi/`. Paths below are written from the project root.
- Leave any legacy `.harness/` directory untouched.

## 1. Gather what happened

Collect candidates from three sources:

- **This conversation:** bugs found or fixed, and their exact error text. Choices made, with their
  reasons and the alternatives rejected. Facts the user stated that the code cannot know (client,
  server, database, deploy, credentials, people). Numbers measured, with sample size. Traps hit.
  Corrections to anything memory already says.
- **Git:** `git status --short`, `git diff --stat`, and `git log --oneline` for this session's commits.
- **Memory as it stands:** `mimi/STATE.md`, and the files the work touched, found through the
  `mimi/MIMI.md` index.

## 2. Filter

For each candidate, ask: *could someone learn this in under a minute by reading the code or running a
command?* If yes, drop it. Ask it of each fact on its own, not of the message the fact came in. A number,
date, measurement, deadline, decision or constraint that a person stated is never derivable from the
code, even when the code touches the same topic: "CI runs Oracle 19c on a self-hosted runner with a
45-minute timeout" keeps the runner and the timeout even though the code shows 19c is supported. Also
drop:
- session narration ("today we looked at…")
- descriptions of how the code works
- finished work that git already records

Scope is never a reason to drop. A fact the user states about their own deployment, infrastructure,
vendors, team, owners, deadlines or downstream use of this code is project memory, even when this
repository's code never touches it: "our ingest service runs this on Lambda, where only /tmp is writable"
is kept. The code cannot tell a future session that, so it is exactly what memory is for. The only
reasons to drop are the three above, the one-minute test, and nothing checkable behind the fact. A fact
a person states is checkable as "told <date>".

A session with nothing durable in it writes nothing to `mimi/ISSUES.md`, `mimi/decisions.md` or `mimi/memory/`. That is
a correct outcome.

## 3. Route each surviving fact to exactly one place

| Candidate | Goes to | Form |
|---|---|---|
| A bug found or fixed | `mimi/ISSUES.md` | Append in the file's existing entry format. With none, use `## ISS-<n> — <title>` with `Symptom:` (exact text), `Cause:`, `Fix:` (commit hash, or `uncommitted: <files>`), `Test:`, `Status:` |
| A choice someone could argue again | `mimi/decisions.md` | Next `DEC-<n>`: `Why:`, `Rejected:`, `Reverse if:`, `Date:`. If it replaces an older entry, mark that one `Superseded by DEC-<n>` and leave its reasoning intact |
| A correction to something memory already says | Wherever the old value lives | Grep every memory file for the old value and fix it in place, in all of them. Never add the new value beside the old one |
| An external fact, a measurement, a trap, a non-obvious why | `mimi/memory/<topic>.md` | Under its own `##` heading, named the way a future task would describe it (error text, library, table, command), not by topic. Cite a commit, issue ID, command, or date with sample size. Set `Last verified:` to today only if this session actually checked the file's facts; otherwise leave the date |

- Pick the existing memory file whose index line fits. Create a new `mimi/memory/<topic>.md` only when
  no file fits. Split by external boundary or subsystem, never by code folder, and add its line to the
  `mimi/MIMI.md` index.
- A fact with nothing checkable behind it goes to the user as a question in the report, not into a
  file. The same goes for something only inferred from what the user said: ask, do not edit memory.
- A short code comment next to the code is also valid memory for a non-obvious why that belongs to one
  line of code. Do not duplicate it into `mimi/memory/`.

## 4. Index

```bash
python "$ML" index .
```

Run it now, before `mimi/STATE.md` is written, so the state is written against the final index.

## 5. Overwrite `mimi/STATE.md`

Rewrite it entirely, keeping the header comment under `# State`. Do not append.

- `Goal:` one line, unchanged unless the goal changed.
- `Deployed`: what is deployed and where, or `unknown`.
- `Broken`: only what is broken now and was observed, with the symptom.
- `Open threads`: work started and not finished.
- `Next 3`: concrete next actions.
- `Last updated:` today.
- `## Last session (<today>)`, about 10 lines, rewritten every time:
  - `Branch:` the current branch.
  - `Uncommitted:` the project files from `git status --short`, run now, or `none`. `mimi/` is git-ignored
    by default, so it does not appear there.
  - `Stopped at:` the task in one line: which steps are done and which step is next.
  - `Tried, failed:` approaches that were actually tried this session, or that the user said were
    tried, each with the reason. These are the only record of dead ends, so never drop one the user
    mentioned. Write `none` if there were none.
  - `Resume with:` the first concrete action for the next session, such as a command or a file to
    open.

`mimi/STATE.md` says what is happening, not what is known. A fact already written to `mimi/memory/`,
`mimi/decisions.md` or `mimi/ISSUES.md` is referenced there by file (`see mimi/memory/client-db.md`), not
repeated.
Remove anything finished. Stay within 60 lines. Only claim something works if it ran in this session.
A plan the user gave for multi-step work stays in `Stopped at` and `Next 3` until it is done.

Then run `python "$ML" check .`, fix every line it prints, and run it again until it prints
`memory layer clean`.

## 6. Verify

- For each fact written, grep a distinctive phrase from it across `mimi/`. It must appear in one memory
  file, plus at most its `mimi/MIMI.md` index line. Merge any duplicate.
- For each correction, grep the old value and confirm it no longer appears as current.
- Confirm `mimi/STATE.md` holds no finished work.

## 7. Report and stop

Tell the user:
- **Written:** each fact and the file and heading it went to.
- **Corrected:** old value → new value, and in which files.
- **Dropped:** each candidate left out, and why (derivable, narration, nothing checkable).
- **Questions:** facts that need a source before they can be recorded.
- **Check:** the final output of `check`.
Do not commit unless the user asks. `mimi/` is git-ignored by default. If the user deleted
`mimi/.gitignore` to share memory and asks for a commit, name the project facts in the message, never the
memory file names.
