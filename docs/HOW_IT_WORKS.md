# How mimi works

- [The three commands](#the-three-commands)
- [The mimi/ folder](#the-mimi-folder)
- [Rules for what gets written](#rules-for-what-gets-written)
- [The script](#the-script)
- [Usage report](#usage-report)
- [How mimi differs from other memory tools](#how-mimi-differs-from-other-memory-tools)

## The three commands

Written here as Claude Code slash commands. See [INSTALL.md](INSTALL.md#slash-commands-in-each-agent) for
the form each agent uses.

### `/mimi-start`: once per project

Creates `mimi/` and adds one import block to each `CLAUDE.md`, `AGENTS.md` or `GEMINI.md` the project has,
or to a new `CLAUDE.md` and `AGENTS.md` if it has none. It picks a mode:

- **New**, for a project with little history. It creates the files, asks for the project's one-line
  goal, and stops. Memory grows from real bugs and decisions, not from guesses on day one.
- **Adopt**, for an existing project. It reads your old notes, agent instruction files, git history,
  issues and deploy config. It keeps only what passes the [one-minute test](#rules-for-what-gets-written)
  and files each fact in one place. Then it reports what moved and what it dropped. It never deletes
  project documentation, and it deletes old agent notes only with your approval.

Running it again later is optional. It then refreshes the index, runs `check`, compares the last
handoff with the working tree, and briefs you in at most 10 lines on where work stopped.

### `/mimi-close`: end of every work session

Nothing needs to run at the start of a session: the memory loads by itself through your agent's
instruction file. At the end, `/mimi-close`:

1. gathers candidates from the conversation, `git status`, the diff and this session's commits
2. drops anything the code or git already shows
3. routes each remaining fact to exactly one place:
   - a bug goes to `mimi/ISSUES.md`
   - a choice goes to `mimi/decisions.md`
   - a correction is edited in place wherever the old value appears
   - an external fact, measurement or trap goes under its own heading in `mimi/memory/<topic>.md`
4. rewrites `mimi/STATE.md`, including a `## Last session` handoff: branch, uncommitted work, where it
   stopped, what was tried and failed, and how to resume
5. runs `index` and `check`, and reports what it wrote, corrected and dropped

It never commits unless you ask.

### `/mimi-logging`: any time

Shows what mimi costs and what it is used for in this project, and saves the report in `mimi/logs/`. See
[Usage report](#usage-report).

## The mimi/ folder

Everything mimi keeps is in one folder at the project root:

```
CLAUDE.md, AGENTS.md    your agent's instruction file(s); mimi adds one managed block: @mimi/MIMI.md
or GEMINI.md            plus a plain line telling agents without @ imports to read mimi/MIMI.md and STATE.md
mimi/
  .gitignore            "*"  (git ignores the whole folder)
  .ignore               "!*" (agent search tools use ripgrep, which skips git-ignored files; this lets them search mimi/)
  MIMI.md               the map: where to look for what, the rules, the memory index
  STATE.md              now only: goal, deployed, broken, open threads, next 3, Last session handoff
  ISSUES.md             every bug: exact symptom, cause, fix commit, test
  decisions.md          choices someone would argue again: why, what was rejected, what would reverse it
  memory/<topic>.md     external quirks, measurements with date and sample size, traps, non-obvious reasons
  logs/                 reports saved by /mimi-logging
```

| File | Limit | Updated |
|---|---|---|
| `mimi/MIMI.md` | ~100 lines | When the layout changes |
| `mimi/STATE.md` | 60 lines | Rewritten every session |
| `mimi/ISSUES.md` | Append-only | Per bug |
| `mimi/decisions.md` | Short entries | Per decision |
| `mimi/memory/<topic>.md` | 150 lines each | When the topic changes |

The instruction file imports `mimi/MIMI.md`, which imports `mimi/STATE.md`. So every session starts with
the map and the current state already loaded: about 1–2k tokens on a typical project, capped at 16 KB.

**Git.** `mimi/.gitignore` keeps the folder out of git, so your project's own `.gitignore` is never
touched, and memory stays on your machine. To share memory with your team through git, delete
`mimi/.gitignore`.

## Rules for what gets written

**The one-minute test.** Before any line is written: could someone learn this in under a minute from the
code or a command? If yes, it is not written down. The test applies to each fact on its own. A number,
date, decision or constraint that a person states is never "in the code".

**The index replaces grepping.** Each trap in a memory file gets its own heading, named the way a task
would describe it. `memlayer.py index` copies those headings onto the file's line in `mimi/MIMI.md`, so a
task that mentions duplicate webhooks lands on the file that holds that trap:

```markdown
- Touching payments → `mimi/memory/payments.md` — contains: Stripe sends the same webhook event twice; refunds fail on test cards
- About to change an existing choice → `mimi/decisions.md` — empty
```

Files with nothing in them are marked `— empty`, so the agent skips them. A memory miss is never taken as
an answer. The agent falls back to `git log --grep` and the code.

Other rules the agent follows:
- Every fact cites something checkable: a commit, an issue ID, a command, or a date with sample size.
- A wrong line gets fixed or deleted, never a correct one added beside it.
- A code change alone writes nothing. Git has it.
- Never overwrite prose a user wrote. Never delete old memory sources without approval.

## The script

`skills/mimi/memlayer.py` does the mechanical work, and the skills call it for you:

```bash
python memlayer.py init  [dir]   # create mimi/ and the instruction-file import; never overwrites
python memlayer.py index [dir]   # refresh index lines in mimi/MIMI.md, mark empty files; idempotent
python memlayer.py check [dir]   # report rot, exit 1 if any
python memlayer.py stats [dir]   # usage and token report; also saved to mimi/logs/stats-<date>.txt
python memlayer.py selftest      # prints SELFTEST_OK
```

`check` reports:
- files over their line limit
- more than 16 KB loaded into every session
- an instruction file (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`) that no longer imports `mimi/MIMI.md`. A file
  holding `<!-- memory-layer:skip -->` is a document, not an instruction file, and is left alone
- a stale or broken index, or a memory file the index doesn't list
- a missing, malformed, future, duplicated or 90-day-old `Last verified:` date
- an incomplete issue entry
- leftover git conflict markers

The script keeps each file's line endings, touches only text inside its own block, and reports errors as
one line instead of a traceback.

## Usage report

`/mimi-logging` reads the transcripts Claude Code already keeps for the project
(`~/.claude/projects/<project>/*.jsonl`). In other agents it reports the memory section only. mimi
installs no hooks and logs nothing while you work. Each report is printed and saved as
`mimi/logs/stats-<date>.txt`. It covers:

- **Cost:** tokens loaded into every session by the instruction file, `MIMI.md` and `STATE.md`, and that
  total across all sessions since adoption
- **Activity:** sessions, prompts, `/mimi-close` runs, and tokens processed, with cache reads shown
  separately
- **Before and after:** median input tokens, tool calls and searches per prompt, before and after
  adoption, and the estimated tokens saved. Adoption is the first commit that added mimi's block, or the
  first session that ran `init`. The comparison needs three sessions on each side.
- **Use:** how many sessions opened a memory file, and how often each file was read. A file that is never
  read is a candidate to merge or delete.

Illustrative output:

```
Memory
  9 files, 412 lines, 21.6 KB
  loaded into every session: CLAUDE.md + STATE.md ~ 1,480 tokens
  6 issues, 3 decisions, 11 traps in memory/, 1 empty files

Sessions (38 transcripts in ~/.claude/projects/...)
  mimi adopted: 2026-09-02
  since then: 24 sessions, 131 prompts, 19 /mimi-close runs
  spent loading memory: ~35,520 tokens (1,480 x 24 sessions, today's size)

  median per prompt     before     after
  input tokens        61,204.0  47,930.5
  tool calls               6.5       4.0
  searches                 2.5       1.0
  estimated input tokens saved: 1,738,828 (median difference x prompts since adoption; ...)
```

The before-and-after saving compares different tasks, so read it as a trend, not a measurement. The
controlled numbers are in [EVALUATION.md](EVALUATION.md).

## How mimi differs from other memory tools

Most memory tools for coding agents capture sessions automatically and inject summaries back. mimi
records deliberately, at the end of a session, and the result lives in your repository. The table below
compares designs as the projects describe them. It is not a measured comparison.

| | mimi | Claude Code auto-memory | [claude-mem](https://github.com/thedotmack/claude-mem) | [claude-mem-lite](https://github.com/sdsrss/claude-mem-lite) | [agentmemory](https://github.com/rohitg00/agentmemory) | [claude-remember](https://github.com/Digital-Process-Tools/claude-remember) |
|---|---|---|---|---|---|---|
| What gets stored | Facts that pass the one-minute test | Notes the agent decides to save | AI-compressed observations of every tool use | Batched observations, graded by importance | Observations, deduplicated and optionally compressed | Haiku summaries of each session |
| When it writes | `/mimi-close` | During the session, at the agent's discretion | Hooks on every tool call | Hooks | 8 lifecycle hooks | Hooks and session end |
| Storage | Markdown in your repo, reviewable in a diff | Markdown in `~/.claude/projects/<project>/memory/`, outside the repo | SQLite + Chroma | SQLite (FTS5) | Local KV store | Markdown files |
| Loaded at start | `CLAUDE.md` block + `STATE.md`, ~1–2k tokens | A `MEMORY.md` index of the notes | Configurable injected context | 2,000-token budget | 2,000-token budget | Identity, handoff and daily summaries |
| Extra LLM calls | None | None | Every capture is compressed by a model | Batched, on Haiku | Optional compression | Haiku per save |
| Runtime | Python standard library | Built in | Node, Bun, uv, a worker service | Node, SQLite | iii runtime | Python, bash, `jq` |
