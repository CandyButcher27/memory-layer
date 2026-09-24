# Memory Layer

**Project memory for coding agents that stores only what the code can't tell you.**

Coding agents like Claude Code start every session knowing nothing about your project. The usual fix is a
growing pile of notes that describe the code, go stale, and get searched anyway. Memory Layer takes the
opposite approach:
- keep a small memory, and give every file one job
- keep only what the code can't tell you: decisions, incidents, external quirks, measurements, and things
  people said
- add an index that sends each task to the right file

**Evaluated on six codebases, including git, django, cargo, node and go.** It recalls what people told
it far better than a conventional notes setup, at half the cost per answer:

| | Conventional notes | Memory Layer |
|---|---|---|
| Recall of facts people stated, across 5 public repos | 0.29 | **0.79** |
| Recall cost per answer | $0.07 | **$0.03** |
| Memory written for the same work, production project | 100% | **40–52%** |

It doesn't beat plain `git log` at finding past incidents on repos whose commit history already explains
them. See [Evaluation](#evaluation).

---

## What it maintains

| File | Holds | Limit | Updated |
|---|---|---|---|
| `CLAUDE.md` (managed block) | The map: where to look for what, hard rules, the memory index | ~100 lines | When the layout changes |
| `STATE.md` | Now only: goal, deployed, broken, open threads, next 3, and a `Last session` handoff | 60 lines | Rewritten every session |
| `ISSUES.md` | Every bug: exact symptom, cause, fix commit, test | Append-only | Per bug |
| `decisions.md` | Choices someone would argue again: why, what was rejected, what would reverse it | Short entries | Per decision |
| `memory/<topic>.md` | External-system quirks, measurements with date and sample size, traps, non-obvious reasons | 150 lines each | When the topic changes |

`CLAUDE.md` imports `STATE.md`, so every session starts with the current state already loaded.

The index is what replaces grepping. `memlayer.py index` copies each memory file's headings onto its line in
`CLAUDE.md`, and each trap has its own heading, named the way a task would describe it. So a task that
mentions duplicate webhooks lands on the file holding that trap:

```markdown
- Touching payments → `memory/payments.md` — contains: Stripe sends the same webhook event twice; refunds fail on test cards
- About to change an existing choice → `decisions.md` — empty
```

Files with nothing in them are marked `— empty`, so the agent skips them. A memory miss is never treated as
an answer: the agent falls back to `git log --grep` and the code.

**The rule behind every line:** could someone learn this in under a minute from the code or a command? If
yes, it isn't written down. The test is applied to each fact separately. A number, date, decision or
constraint that a person states is never "in the code".

## Quick start

```bash
git clone https://github.com/CandyButcher27/memory-layer
# install as a Claude Code skill and slash command
cp -r memory-layer ~/.claude/skills/memory-layer
cp memory-layer/commands/session-close.md ~/.claude/commands/

# new project: create the files and the CLAUDE.md block (never overwrites anything)
python ~/.claude/skills/memory-layer/memlayer.py init .
```

For an existing project, ask Claude Code to *"adopt the memory layer"*. The skill's **Adopt** mode:
- reads your old notes, `CLAUDE.md`, git history, issues and deploy config
- keeps only what passes the one-minute test and files each fact in one place
- reports what moved and what it dropped
- never deletes project documentation

At the end of every work session, run **`/session-close`**. It writes what the session learned:
- a bug goes to `ISSUES.md`
- a choice goes to `decisions.md`
- a correction is edited in place wherever the old value appears
- an external fact goes to `memory/`

It then rewrites `STATE.md`, runs `index` and `check`, and reports what it wrote and what it left out. It
never commits without being asked.

## Commands

```bash
python memlayer.py init  [dir]   # create missing files and the CLAUDE.md block; never overwrites
python memlayer.py index [dir]   # refresh index lines from headings; mark empty files; idempotent
python memlayer.py check [dir]   # report rot, exit 1 if any
python memlayer.py selftest      # prints SELFTEST_OK
```

`check` reports:
- files over their line limit
- more than 16 KB loaded into every session
- a stale or broken index
- a memory file the index doesn't list
- a missing, malformed, future, duplicated or 90-day-old `Last verified:` date
- an incomplete issue entry
- leftover git conflict markers

`memlayer.py` is standard-library Python with no dependencies. It keeps each file's own line endings, only
touches text inside its own block, and reports errors as one line instead of a traceback.

---

## Evaluation

Seven experiments on six codebases, a stress-test suite, and every failure fixed and re-tested. The full
method, per-task results and raw verdicts are in [`docs/EVALUATION.md`](docs/EVALUATION.md).

### How it was measured

- **Arms:**
  - **no memory**, as a control
  - **conventional notes**: a `memory/<component>.md` knowledge base plus a `CLAUDE.md`, built by a
    harness skill that describes each subsystem
  - **Memory Layer**
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

| Repository | Conventional notes | Memory Layer |
|---|---|---|
| git/git (C, 82k commits) | 0.32 | **0.72** |
| django/django (Python, 35k) | 0.33 | **0.44** |
| rust-lang/cargo (Rust, 23k) | 0.15 | **1.00** |
| nodejs/node (JS/C++, 49k) | 0.37 | **0.80** |
| golang/go (Go, 68k) | 0.28 | **1.00** |
| **Mean** | 0.29 | **0.79** |

Memory Layer won on every repository, at about half the cost per answer and with far fewer wrong claims.
The conventional setup mostly wrote descriptions of code the agent had just looked up. It lost what people
said, and it filled the gaps with plausible values from the repo.

**Retrieval: past incidents from commit history, 10 questions × 2 runs each:**

| Repository | No memory | Conventional notes | Memory Layer |
|---|---|---|---|
| git/git | 0.77 | **0.80** | 0.63 |
| django/django | **0.82** | **0.82** | 0.73 |
| rust-lang/cargo | **0.83** | 0.74 | 0.74 |
| nodejs/node | 0.80 | 0.86 | **0.90** |
| golang/go | 0.81 | 0.81 | 0.80 |
| **Mean** | **0.81** | **0.81** | 0.76 |

On repositories with detailed commit histories, no memory setup beats `git log --grep` at finding past
incidents. Memory Layer came out lower there for a traceable reason: a memory built cold from such a
repository is thin, and the agent read its empty files before searching git. The `— empty` markers and the
fall-back rule were added in response. **They have not yet been re-evaluated on these repositories.**

### One production project (171 commits, real memory already in place)

Here the conventional setup's memory was about 4,600 lines built up over months. Memory Layer's **Adopt**
mode rebuilt it into 744.

| | No memory | Conventional notes | Memory Layer |
|---|---|---|---|
| Retrieval, Sonnet (12 tasks × 2) | 0.86 | 0.93 | **0.93** |
| Retrieval, Opus | – | 0.99 | **1.00** |
| Recall after 6 work sessions, Opus | – | 1.00 | **1.00** |
| Memory lines written in those sessions | – | +262 | **+135** |
| Recall cost per answer | – | $0.11 | **$0.08** |
| Wrong claims per recall answer (Sonnet) | – | 0.20 | **0.07** |

Two results changed the design:
- **The index.** Before `index` existed, Memory Layer held a fact in `memory/external.md` but never opened
  the file, because its index line didn't mention transactions. Retrieval was 0.88. Generating index lines
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
| S3: `/session-close` under adversarial sessions | Pasted secrets, a bug fix, a reversed decision, a silent contradiction, a private detail, running it twice | Secrets and private details were never stored. A step-ordering bug was found and fixed |
| S4: design limits | Parallel sessions, auto-loaded size, renamed headings | A 16 KB cap and stale-index detection were added |

### Limitations

- **Retrieval:** on public repositories it was slightly worse than no memory (0.76 against 0.81). The
  fixes for that are applied but not yet re-measured.
- **Scale:** each repository run has 15–20 answers per arm, so differences under about 0.1 are within
  noise.
- **Test facts:** the write-and-recall facts were written for the test, and only 5–6 sessions ran per
  arm. Drift over months of real use is untested.
- **Parallel work:** two sessions closing on separate branches conflict in `STATE.md`. `check` catches
  leftover conflict markers, but the conflict itself comes from having a single current-state file.

---

## Repository layout

```
SKILL.md  memlayer.py  templates/  commands/   the skill; installs as one folder
AGENTS.md                                      what the agent does, for agents
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
