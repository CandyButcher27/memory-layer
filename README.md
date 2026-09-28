# mimi

**A memory agent for Claude Code that remembers only what your code can't tell it.**

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![Dependencies: none](https://img.shields.io/badge/dependencies-none-brightgreen)
![Storage: markdown in your repo](https://img.shields.io/badge/storage-markdown%20in%20your%20repo-lightgrey)

Coding agents start every session knowing nothing about your project. Most memory tools fix this by
recording everything the agent does and replaying summaries of it. mimi does the opposite. It keeps a
small, reviewed memory inside your repository and gives every file one job. It stores only the things
that are not in the code: bugs and their causes, decisions and the options you rejected, quirks of
external systems, measured numbers, and what people told the agent.

On five large public repositories (git, django, cargo, node and go), mimi recalled what people said
during work sessions far better than a conventional notes setup, at less than half the cost per answer:

| | Conventional notes | mimi |
|---|---|---|
| Recall of facts people stated, mean of 5 public repos | 0.29 | **0.79** |
| Recall cost per answer | $0.07 | **$0.03** |
| Memory written for the same work, production project | 100% | **40–52%** |

It does not beat plain `git log` at finding past incidents on repositories whose commit messages
already explain them. See [Evaluation](#evaluation) for the method and every number.

---

## Contents

- [Install](#install)
- [Usage](#usage)
- [How it works](#how-it-works)
- [Usage report](#usage-report)
- [How mimi differs from other memory tools](#how-mimi-differs-from-other-memory-tools)
- [Evaluation](#evaluation)
- [Limitations](#limitations)
- [Repository layout](#repository-layout)

## Install

mimi is a Claude Code skill, three slash commands and one standard-library Python script. There is no
server, database, background process or package to install.

```bash
git clone https://github.com/CandyButcher27/memory-layer
cd memory-layer
mkdir -p ~/.claude/skills/mimi ~/.claude/commands
cp -r SKILL.md memlayer.py templates ~/.claude/skills/mimi/
cp commands/mimi-*.md ~/.claude/commands/
python ~/.claude/skills/mimi/memlayer.py selftest    # prints SELFTEST_OK
```

## Usage

| Command | When | What it does |
|---|---|---|
| `/mimi-start` | Start of a session | Sets the project up if it has no memory yet. Otherwise refreshes the index, checks for rot, and briefs you on where the last session stopped |
| `/mimi-close` | End of a session | Writes what the session learned to the right file, rewrites the current state, and checks the result |
| `/mimi-logging` | Any time | Shows what mimi costs and what it is used for in this project, from your Claude Code session logs |

**First run.** `/mimi-start` picks a mode:
- **New**, for a project with little history. It creates the files, asks for the project's one-line
  goal, and stops. Memory grows from real bugs and decisions, not from guesses on day one.
- **Adopt**, for an existing project. It reads your old notes, `CLAUDE.md`, git history, issues and
  deploy config. It keeps only what passes the one-minute test (below) and files each fact in one
  place. Then it reports what moved and what it dropped. It never deletes project documentation, and it
  deletes old agent notes only with your approval.

**Every session after that.** Run `/mimi-start` when you begin and `/mimi-close` when you stop.
`/mimi-close` sends a bug to `ISSUES.md` and a choice to `decisions.md`. It edits a correction in place
wherever the old value appears, and it puts an external fact under its own heading in `memory/`. It
never commits unless you ask.

## How it works

mimi maintains five kinds of file in your project:

| File | Holds | Limit | Updated |
|---|---|---|---|
| `CLAUDE.md` (managed block) | The map: where to look for what, the rules, and the memory index | ~100 lines | When the layout changes |
| `STATE.md` | Now only: goal, deployed, broken, open threads, next 3, and a `Last session` handoff | 60 lines | Rewritten every session |
| `ISSUES.md` | Every bug: exact symptom, cause, fix commit, test | Append-only | Per bug |
| `decisions.md` | Choices someone would argue again: why, what was rejected, what would reverse it | Short entries | Per decision |
| `memory/<topic>.md` | External-system quirks, measurements with date and sample size, traps, non-obvious reasons | 150 lines each | When the topic changes |

`CLAUDE.md` imports `STATE.md`, so every session starts with the current state already loaded. That is
about 1–2k tokens on a typical project, capped at 16 KB.

**The one-minute test.** Before any line is written: could someone learn this in under a minute from the
code or a command? If yes, it is not written down. The test applies to each fact on its own. A number,
date, decision or constraint that a person states is never "in the code".

**The index replaces grepping.** Each trap in a memory file gets its own heading, named the way a task
would describe it. `memlayer.py index` copies those headings onto the file's line in `CLAUDE.md`, so a
task that mentions duplicate webhooks lands on the file that holds that trap:

```markdown
- Touching payments → `memory/payments.md` — contains: Stripe sends the same webhook event twice; refunds fail on test cards
- About to change an existing choice → `decisions.md` — empty
```

Files with nothing in them are marked `— empty`, so the agent skips them. A memory miss is never taken as
an answer. The agent falls back to `git log --grep` and the code.

### Script

`memlayer.py` does the mechanical work, and the slash commands call it for you:

```bash
python memlayer.py init  [dir]   # create missing files and the CLAUDE.md block; never overwrites
python memlayer.py index [dir]   # refresh index lines from headings, mark empty files; idempotent
python memlayer.py check [dir]   # report rot, exit 1 if any
python memlayer.py stats [dir]   # usage and token report from Claude Code session logs
python memlayer.py selftest      # prints SELFTEST_OK
```

`check` reports:
- files over their line limit
- more than 16 KB loaded into every session
- a stale or broken index, or a memory file the index doesn't list
- a missing, malformed, future, duplicated or 90-day-old `Last verified:` date
- an incomplete issue entry
- leftover git conflict markers

The script keeps each file's line endings, touches only text inside its own block, and reports errors as
one line instead of a traceback.

## Usage report

`/mimi-logging` reads the transcripts Claude Code already keeps for the project
(`~/.claude/projects/<project>/*.jsonl`). mimi installs no hooks and logs nothing of its own. The report
covers:

- **Cost:** tokens loaded into every session by `CLAUDE.md` and `STATE.md`, and that total across all
  sessions since adoption
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
controlled numbers are in [Evaluation](#evaluation).

## How mimi differs from other memory tools

Most memory tools for coding agents capture sessions automatically and inject summaries back. mimi
records deliberately, at the end of a session, and the result lives in your repository. The table below
compares designs as the projects describe them. It is not a measured comparison.

| | mimi | [claude-mem](https://github.com/thedotmack/claude-mem) | [claude-mem-lite](https://github.com/sdsrss/claude-mem-lite) | [agentmemory](https://github.com/rohitg00/agentmemory) | [claude-remember](https://github.com/Digital-Process-Tools/claude-remember) |
|---|---|---|---|---|---|
| What gets stored | Facts that pass the one-minute test | AI-compressed observations of every tool use | Batched observations, graded by importance | Observations, deduplicated and optionally compressed | Haiku summaries of each session |
| When it writes | `/mimi-close` | Hooks on every tool call | Hooks | 8 lifecycle hooks | Hooks and session end |
| Storage | Markdown in your repo, reviewable in a diff | SQLite + Chroma | SQLite (FTS5) | Local KV store | Markdown files |
| Loaded at start | `CLAUDE.md` block + `STATE.md`, ~1–2k tokens | Configurable injected context | 2,000-token budget | 2,000-token budget | Identity, handoff and daily summaries |
| Extra LLM calls | None | Every capture is compressed by a model | Batched, on Haiku | Optional compression | Haiku per save |
| Runtime | Python standard library | Node, Bun, uv, a worker service | Node, SQLite | iii runtime | Python, bash, `jq` |

## Evaluation

Seven experiments on six codebases, a stress-test suite, and every failure fixed and re-tested. The full
method, per-task results and raw verdicts are in [`docs/EVALUATION.md`](docs/EVALUATION.md). The
experiments ran before the rename, so the documents call mimi "the memory layer" and its close command
`/session-close`.

### Method

- **Arms:**
  - **no memory**, as a control
  - **conventional notes:** a `memory/<component>.md` knowledge base plus a `CLAUDE.md`, built by a
    harness skill that describes each subsystem
  - **mimi**
- **Answer keys never come from either memory system.** Retrieval questions are written from raw commit
  messages and diffs before any memory exists. Recall questions test facts stated during the sessions.
- **Two independent judges**, Sonnet and Opus, grade every answer against the key. Each judge must quote
  the evidence for each key point before giving a verdict. They agree on 95–100% of key points.
- **Every task runs in a fresh, headless `claude -p` session.** Metrics come from the session stream:
  tool calls, searches, input tokens, cost and time.

### Five large public repositories

One agent per repository, each on its own GitHub Codespace, all under one
[protocol](eval/public/PROTOCOL.md). The task model is Sonnet, and both memory arms were built by Opus.

**Recall: facts people stated during 5 work sessions, 5 questions × 3 runs each:**

| Repository | Conventional notes | mimi |
|---|---|---|
| git/git (C, 82k commits) | 0.32 | **0.72** |
| django/django (Python, 35k) | 0.33 | **0.44** |
| rust-lang/cargo (Rust, 23k) | 0.15 | **1.00** |
| nodejs/node (JS/C++, 49k) | 0.37 | **0.80** |
| golang/go (Go, 68k) | 0.28 | **1.00** |
| **Mean** | 0.29 | **0.79** |

mimi won on every repository, at about half the cost per answer and with far fewer wrong claims. The
conventional setup mostly wrote descriptions of code the agent had just looked up. It lost what people
said, and it filled the gaps with plausible values from the repo.

**Retrieval: past incidents from commit history, 10 questions × 2 runs each:**

| Repository | No memory | Conventional notes | mimi |
|---|---|---|---|
| git/git | 0.77 | **0.80** | 0.63 |
| django/django | **0.82** | **0.82** | 0.73 |
| rust-lang/cargo | **0.83** | 0.74 | 0.74 |
| nodejs/node | 0.80 | 0.86 | **0.90** |
| golang/go | 0.81 | 0.81 | 0.80 |
| **Mean** | **0.81** | **0.81** | 0.76 |

On repositories with detailed commit histories, no memory setup beats `git log --grep` at finding past
incidents. mimi came out lower there for a traceable reason: a memory built cold from such a repository
is thin, and the agent read its empty files before searching git. The `— empty` markers and the
fall-back rule were added in response. **They have not yet been re-evaluated on these repositories.**

### One production project (171 commits, real memory already in place)

Here the conventional setup's memory was about 4,600 lines built up over months. mimi's **Adopt** mode
rebuilt it into 744.

| | No memory | Conventional notes | mimi |
|---|---|---|---|
| Retrieval, Sonnet (12 tasks × 2) | 0.86 | 0.93 | **0.93** |
| Retrieval, Opus | – | 0.99 | **1.00** |
| Recall after 6 work sessions, Opus | – | 1.00 | **1.00** |
| Memory lines written in those sessions | – | +262 | **+135** |
| Recall cost per answer | – | $0.11 | **$0.08** |
| Wrong claims per recall answer (Sonnet) | – | 0.20 | **0.07** |

Two results changed the design:
- **The index.** Before `index` existed, mimi held a fact in `memory/external.md` but never opened the
  file, because its index line didn't mention transactions. Retrieval was 0.88. Generating index lines
  from headings brought it to 0.93. Two attempts to make the agent write better index lines by
  instruction alone failed.
- **The handoff.** With a `Last session` section, the dead end a user mentioned was recorded in 3 of 3
  closes. Without it, 1 of 3, and one run went on to reopen a decision the user had already made.

### Stress tests

The pass conditions were written before any test ran. See [`docs/STRESS_TESTS.md`](docs/STRESS_TESTS.md).

| Area | What it covered | Result |
|---|---|---|
| S1: script edge cases | Line endings, Unicode, invalid dates, odd file names, read-only files, 40 memory files, conflict markers | 33 of 33 pass (was 16 of 28 before fixes) |
| S2: Adopt on 4 other projects | No prior memory, an old notes setup, a tiny repo, a C repo, a second Adopt run | 28 facts checked, none false. A deletion of project docs was found and fixed |
| S3: closing under adversarial sessions | Pasted secrets, a bug fix, a reversed decision, a silent contradiction, a private detail, running it twice | Secrets and private details were never stored. A step-ordering bug was found and fixed |
| S4: design limits | Parallel sessions, auto-loaded size, renamed headings | A 16 KB cap and stale-index detection were added |

## Limitations

- **Retrieval:** on public repositories it was slightly worse than no memory (0.76 against 0.81). The
  fixes for that are applied but not yet re-measured.
- **Scale:** each repository run has 15–20 answers per arm, so differences under about 0.1 are within
  noise.
- **Test facts:** the write-and-recall facts were written for the test, and only 5–6 sessions ran per
  arm. Drift over months of real use is untested.
- **No head-to-head yet:** mimi has not been measured against claude-mem or the other tools above.
- **Parallel work:** two sessions closing on separate branches conflict in `STATE.md`. `check` catches
  leftover conflict markers, but the conflict itself comes from having a single current-state file.
- **Manual close:** memory is only as current as the last `/mimi-close`. `/mimi-logging` shows how many
  sessions ended without one.

## Repository layout

```
SKILL.md  memlayer.py  templates/   the skill; installs as one folder
commands/     mimi-start.md, mimi-close.md, mimi-logging.md
AGENTS.md     what the agent does, written for agents
docs/         EVALUATION.md, STRESS_TESTS.md
eval/
  harness/    run.py (runner and dual judge), hygiene.py, build_d.py, handoff.sh
  tasks/      retrieval, session, recall and handoff task files with answer keys
  the production project/    production-project runs and reports
  public/     PROTOCOL.md and per-repository results (git, django, cargo, node, go)
  stress/     S1–S3 suites and results
```

Raw agent transcripts are not committed. The repository keeps the scripts, task files, per-answer judge
verdicts, memory snapshots and written reports.
