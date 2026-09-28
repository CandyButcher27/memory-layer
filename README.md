# mimi

**A memory agent for Claude Code that remembers only what your code can't tell it.**

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![Dependencies: none](https://img.shields.io/badge/dependencies-none-brightgreen)
![Storage: markdown in your repo](https://img.shields.io/badge/storage-markdown%20in%20your%20repo-lightgrey)

Coding agents start every session knowing nothing about your project. Most memory tools fix this by
recording everything the agent does and replaying summaries of it. mimi does the opposite. It keeps a
small, reviewed memory in one `mimi/` folder inside your project, and gives every file one job. It stores only the things
that are not in the code: bugs and their causes, decisions and the options you rejected, quirks of
external systems, measured numbers, and what people told the agent.

The baseline to beat is Claude Code's own built-in auto-memory. On two repositories (rust-lang/cargo and
simonw/sqlite-utils), with the pass criteria committed before the run, mimi led on both jobs tested:

| | No memory | Built-in auto-memory | claude-mem | mimi |
|---|---|---|---|---|
| Recalling facts people mentioned in passing (48 answers) | 0.09 | 0.51 | 0.15 | **0.83** |
| Wrong claims per answer on those facts | 0.77 | 0.21 | 0.56 | **0.02** |
| Resuming unfinished work (20 answers) | 0.39 | 0.80 | 0.42 | **0.97** |
| Cost per answer | $0.06–0.07 | $0.04 | $0.08–0.09 | **$0.03** |

Where this is thin:
- The lead over auto-memory on resuming work rests on only 4 questions.
- Writing memory costs more: each `/mimi-close` is about $0.48.
- mimi does not beat plain `git log` at finding past incidents in repositories whose commit messages
  already explain them.

The same run found a bug in `/mimi-close`, now fixed but not yet re-measured. See
[Evaluation](#evaluation) for the method and every number.

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
| `/mimi-start` | Once per project | Sets the project up: creates `mimi/` and adds one import line to `CLAUDE.md`. Running it again later is optional and only gives a brief of where the last session stopped |
| `/mimi-close` | End of a work session | Writes what the session learned to the right file, rewrites the current state, and checks the result |
| `/mimi-logging` | Any time | Shows what mimi costs and what it is used for in this project, from your Claude Code session logs, and saves the report in `mimi/logs/` |

**Setup, once.** `/mimi-start` picks a mode:
- **New**, for a project with little history. It creates the files, asks for the project's one-line
  goal, and stops. Memory grows from real bugs and decisions, not from guesses on day one.
- **Adopt**, for an existing project. It reads your old notes, `CLAUDE.md`, git history, issues and
  deploy config. It keeps only what passes the one-minute test (below) and files each fact in one
  place. Then it reports what moved and what it dropped. It never deletes project documentation, and it
  deletes old agent notes only with your approval.

**Every session after that.** Nothing to run at the start: the memory loads by itself through
`CLAUDE.md`. Run `/mimi-close` when you stop:
- a bug goes to `mimi/ISSUES.md`
- a choice goes to `mimi/decisions.md`
- a correction is edited in place wherever the old value appears
- an external fact goes under its own heading in `mimi/memory/`

It never commits unless you ask.

## How it works

Everything mimi keeps is in one folder at the project root:

```
CLAUDE.md               your file; mimi adds one managed line: @mimi/MIMI.md
mimi/
  .gitignore            "*"  (git ignores the whole folder)
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

`CLAUDE.md` imports `mimi/MIMI.md`, which imports `mimi/STATE.md`. So every session starts with the map
and the current state already loaded: about 1–2k tokens on a typical project, capped at 16 KB.

**Git.** `mimi/.gitignore` keeps the folder out of git, so your project's own `.gitignore` is never
touched, and memory stays on your machine. To share memory with your team through git, delete
`mimi/.gitignore`.

**The one-minute test.** Before any line is written: could someone learn this in under a minute from the
code or a command? If yes, it is not written down. The test applies to each fact on its own. A number,
date, decision or constraint that a person states is never "in the code".

**The index replaces grepping.** Each trap in a memory file gets its own heading, named the way a task
would describe it. `memlayer.py index` copies those headings onto the file's line in `CLAUDE.md`, so a
task that mentions duplicate webhooks lands on the file that holds that trap:

```markdown
- Touching payments → `mimi/memory/payments.md` — contains: Stripe sends the same webhook event twice; refunds fail on test cards
- About to change an existing choice → `mimi/decisions.md` — empty
```

Files with nothing in them are marked `— empty`, so the agent skips them. A memory miss is never taken as
an answer. The agent falls back to `git log --grep` and the code.

### Script

`memlayer.py` does the mechanical work, and the slash commands call it for you:

```bash
python memlayer.py init  [dir]   # create mimi/ and the CLAUDE.md import; never overwrites
python memlayer.py index [dir]   # refresh index lines in mimi/MIMI.md, mark empty files; idempotent
python memlayer.py check [dir]   # report rot, exit 1 if any
python memlayer.py stats [dir]   # usage and token report; also saved to mimi/logs/stats-<date>.txt
python memlayer.py selftest      # prints SELFTEST_OK
```

`check` reports:
- files over their line limit
- more than 16 KB loaded into every session
- a `CLAUDE.md` that no longer imports `mimi/MIMI.md`
- a stale or broken index, or a memory file the index doesn't list
- a missing, malformed, future, duplicated or 90-day-old `Last verified:` date
- an incomplete issue entry
- leftover git conflict markers

The script keeps each file's line endings, touches only text inside its own block, and reports errors as
one line instead of a traceback.

## Usage report

`/mimi-logging` reads the transcripts Claude Code already keeps for the project
(`~/.claude/projects/<project>/*.jsonl`). mimi installs no hooks and logs nothing while you work. Each
report is printed and saved as `mimi/logs/stats-<date>.txt`. It covers:

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

| | mimi | Claude Code auto-memory | [claude-mem](https://github.com/thedotmack/claude-mem) | [claude-mem-lite](https://github.com/sdsrss/claude-mem-lite) | [agentmemory](https://github.com/rohitg00/agentmemory) | [claude-remember](https://github.com/Digital-Process-Tools/claude-remember) |
|---|---|---|---|---|---|---|
| What gets stored | Facts that pass the one-minute test | Notes the agent decides to save | AI-compressed observations of every tool use | Batched observations, graded by importance | Observations, deduplicated and optionally compressed | Haiku summaries of each session |
| When it writes | `/mimi-close` | During the session, at the agent's discretion | Hooks on every tool call | Hooks | 8 lifecycle hooks | Hooks and session end |
| Storage | Markdown in your repo, reviewable in a diff | Markdown in `~/.claude/projects/<project>/memory/`, outside the repo | SQLite + Chroma | SQLite (FTS5) | Local KV store | Markdown files |
| Loaded at start | `CLAUDE.md` block + `STATE.md`, ~1–2k tokens | A `MEMORY.md` index of the notes | Configurable injected context | 2,000-token budget | 2,000-token budget | Identity, handoff and daily summaries |
| Extra LLM calls | None | None | Every capture is compressed by a model | Batched, on Haiku | Optional compression | Haiku per save |
| Runtime | Python standard library | Built in | Node, Bun, uv, a worker service | Node, SQLite | iii runtime | Python, bash, `jq` |

## Evaluation

Eight experiments on seven codebases, a stress-test suite, and every failure fixed and re-tested.
- The latest, Stage 1, is in [`eval/stage1/RESULTS.md`](eval/stage1/RESULTS.md).
- The earlier ones are in [`docs/EVALUATION.md`](docs/EVALUATION.md). They ran before the rename, so
  those documents call mimi "the memory layer" and its close command `/session-close`.

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

### Stage 1: against built-in auto-memory and claude-mem

[`PREREG.md`](eval/stage1/PREREG.md) fixed the arms, tasks and decision rules before any run, and it
was committed first.

- **Arms:**
  - no memory
  - Claude Code's built-in auto-memory
  - mimi, with each work session ending in `/mimi-close`
  - claude-mem 13.28.0
- **Isolation:** each arm had its own `HOME` and a logging proxy, so every model call was counted,
  including claude-mem's background Haiku worker. Every eval run started from the same saved state.
- **Repositories:** rust-lang/cargo and simonw/sqlite-utils.
- **Two task families:**
  - **Stated facts:** 8 facts per repo, mentioned in passing inside multi-turn work sessions next to
    noise. One of them is corrected later. 8 questions × 3 runs per repo.
  - **Continuity:** a feature left half-done and an investigation left mid-way, each resumed in a fresh
    session. 2 questions × 5 runs per repo.

| | No memory | Auto-memory | claude-mem | mimi |
|---|---|---|---|---|
| Stated facts, accuracy | 0.09 | 0.51 | 0.15 | **0.83** |
| Stated facts, wrong claims per answer | 0.77 | 0.21 | 0.56 | **0.02** |
| Continuity, accuracy | 0.39 | 0.80 | 0.42 | **0.97** |
| Context tokens per answer | 160–171k | 84–125k | 170–201k | **63–69k** |

Paired differences, with 95% bootstrap intervals over questions:
- **mimi − claude-mem:** +0.68 [+0.41, +0.88] on stated facts, +0.55 [+0.21, +0.89] on continuity.
- **mimi − auto-memory:** +0.32 [+0.10, +0.55] on stated facts, +0.17 [+0.02, +0.33] on continuity.

Every pre-registered rule for a mimi win was met. The continuity interval rests on only 4 questions.

What the transcripts show:
- **claude-mem kept code, not conversation.** Its observations were descriptions of code the agent had
  read. It processed an investigation session in over 10 batches and stored nothing ("routine code
  navigation"), so the user's ruled-out hypotheses were lost.
- **Auto-memory kept every decision, deadline and review rule.** It missed measurements, people and
  infrastructure details, and it made the most wrong claims on continuity.
- **mimi's two misses were its own bug.** `/mimi-close` dropped two facts the user stated as being "about
  your downstream service, not this repo". Commit `3bdb281` makes scope never a reason to drop.
  [`PREREG-2.md`](eval/stage1/PREREG-2.md) pre-registers a re-run of that repo, plus 8 more continuity
  questions. **Neither has run yet.**

Stage 1 cost about $50. An earlier single-repo pilot against claude-mem and claude-mem-lite is in
[`eval/public/cargo/pilot/RESULTS.md`](eval/public/cargo/pilot/RESULTS.md).

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
- **Continuity:** the lead over built-in auto-memory rests on 4 questions, with a lower bound of +0.02.
  Eight more are pre-registered and have not run.
- **The `/mimi-close` scope fix is not re-measured.** Before the fix, it dropped facts about the user's own
  systems. The fix (`3bdb281`) passes the self-test but has not been re-run against the tasks that
  exposed the bug.
- **Write cost:** each `/mimi-close` costs about $0.48. mimi is the cheapest per answer, but closing every
  session is not free.
- **Who wrote the tests:** I wrote the facts and sessions for every experiment. Stage 1 reduced the home
  advantage (facts come up in passing, and continuity is automatic capture's strength), but did not
  remove it.
- **Parallel work:** two sessions closing on separate branches conflict in `STATE.md`. `check` catches
  leftover conflict markers, but the conflict itself comes from having a single current-state file.
- **Local by default:** `mimi/` is git-ignored, so memory is not shared with teammates or backed up by
  git unless you delete `mimi/.gitignore`. The evaluations above tracked the memory files in the
  repository. The only difference is where the files live, since Claude Code loads imported files either
  way.
- **Manual close:** memory is only as current as the last `/mimi-close`. `/mimi-logging` shows how many
  sessions ended without one.

## Repository layout

```
SKILL.md  memlayer.py  templates/   the skill; installs as one folder (templates/ seeds a project's mimi/)
commands/     mimi-start.md, mimi-close.md, mimi-logging.md
AGENTS.md     what the agent does, written for agents
docs/         EVALUATION.md, STRESS_TESTS.md
eval/
  harness/    run.py (runner and dual judge), stage1.sh and pilot.sh (drivers), proxy.py (token
              logging proxy), tokens.py (token accounting), analyze.py (bootstrap analysis),
              hygiene.py, build_d.py, handoff.sh
  stage1/     pre-registrations, task files and results for the comparison with auto-memory
              and claude-mem
  tasks/      retrieval, session, recall and handoff task files with answer keys
  the production project/    production-project runs and reports
  public/     PROTOCOL.md, per-repository results (git, django, cargo, node, go), and the
              cargo competitor pilot
  stress/     S1–S3 suites and results
```

Raw agent transcripts are not committed. The repository keeps the scripts, task files, per-answer judge
verdicts, memory snapshots and written reports.
