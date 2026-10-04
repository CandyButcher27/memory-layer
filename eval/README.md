# How mimi is evaluated

This folder holds every evaluation of mimi: the harnesses, the task files, the pre-registrations, every answer
with its verdict, and the results. This page explains the method once. Each experiment's own files hold its
numbers.

## What is being measured

A memory tool for coding agents is worth having if a later session can answer questions that the code alone
cannot answer. So every evaluation has the same shape:

1. **Write phase.** An agent works on a real repository over one or more sessions. During that work, people
   mention facts, the agent finds things, plans change, work is left unfinished. Each memory tool records
   whatever it records.
2. **Eval phase.** A fresh session, with only what the memory tool kept, is asked questions about that earlier
   work.
3. **Judging.** A separate model grades each answer against an answer key.

The arms differ only in the memory tool. Everything else is held the same.

## The arms

| Arm | Memory |
|---|---|
| A | None. Claude Code's auto-memory is turned off. The floor |
| N | Claude Code's built-in auto-memory. What every user has by default |
| D | mimi, with `/mimi-close` at the end of every work session, as documented |
| D0 | mimi, never closed. What happens when the user forgets |
| M | [claude-mem](https://github.com/thedotmack/claude-mem) |
| G | [agentmemory](https://github.com/rohitg00/agentmemory) |
| R | claude-remember (Digital-Process-Tools) |
| L | claude-mem-lite (sdsrss) |
| K | [recall](https://github.com/raiyanyahya/recall) |

Every rival runs with its default settings, installed the way its README says. Every arm except N runs with
auto-memory off, so each arm tests one tool.

## The repositories, and why these

| Repository | Commit | Why |
|---|---|---|
| [simonw/sqlite-utils](https://github.com/simonw/sqlite-utils) | `6bc1d33` | A small Python app with terse commit messages, so git history explains little |
| [rust-lang/cargo](https://github.com/rust-lang/cargo) | `694054f` | A large Rust project with detailed commit messages. A harder test for memory, because `git log` already explains a lot |

Each repository is pinned to one commit, so every arm sees the same code, the answer keys stay correct, and
the results can be reproduced and compared across experiments. An earlier experiment also used git, django,
node and go (Experiment 7 in [`../docs/EVALUATION.md`](../docs/EVALUATION.md)).

## The kinds of questions

| Family | What happens in the sessions | Example question |
|---|---|---|
| Stated | The user mentions a fact in passing, next to a real code question: a person, a limit, a decision, a deadline, a review rule, a measurement, an infrastructure detail, a trap | "Who should be paged first when the ingest service breaks?" |
| Corrected | A fact changes later, once or twice | "What time does the nightly batch start?", after it moved |
| Discovered | The agent reads a file outside the repo, which is deleted afterwards. The user never states the answer | A detail from a failure log the agent was asked to read |
| Continuity | Work is left unfinished: a feature half-built, an investigation mid-way, a plan reversed, review feedback partly done | "Where did we get to, and what's next?" |
| Repo | Answerable from the code alone. A control for cost, not memory | |

Stated facts and continuity are what a memory tool is for. The discovered family is where tools that record
everything automatically should beat mimi, and it is there on purpose.

## How a run works

- **Headless sessions.** Every session is `claude -p` with a fixed model and `--max-turns 40`, so no person
  steers the agent.
- **Isolation.** Each arm gets its own `HOME` and its own copy of the repository, so no tool can see another's
  store. Each tool's background process is stopped between jobs.
- **Same starting point for every answer.** After the write phase, each arm's state is saved. Every eval
  answer starts from that saved state, so no answer sees another answer's session.
- **Tool-agnostic answer keys.** Keys are written from the session scripts and the code before any memory
  exists, never from a memory tool's output.
- **Judging.** The judge has no tools. For each key point it quotes the evidence from the answer before it
  gives a verdict, then counts wrong claims. Accuracy is the share of key points hit.
- **Statistics.** Arms are compared on the same question and run. The 95% interval is a bootstrap over
  questions, so a result that rests on one lucky question shows a wide interval.
- **Pre-registration.** Each experiment's questions, arms and decision rules (what counts as a win, a tie or a
  loss) are committed before the first result. Any later change is recorded as a deviation, with its reason.

## Metrics

| Metric | Meaning |
|---|---|
| Accuracy | Share of answer-key points the judge finds in the answer |
| Wrong claims | Claims per answer that the judge marks false or contradicting the key |
| Tokens, tool calls | How much the agent had to read and search to answer |
| Cost | Claude Code's `total_cost_usd` per answer, and per write session |

## The experiments

| Experiment | Question | Where |
|---|---|---|
| 1–6 | Does mimi match a conventional notes setup on a private production project, with less memory? | [`../docs/EVALUATION.md`](../docs/EVALUATION.md) (aggregates only; the project is private) |
| 7 | Does it hold on five large public repos (git, django, cargo, node, go)? | [`public/`](public/), protocol in [`public/PROTOCOL.md`](public/PROTOCOL.md) |
| 8: Stage 1 | Against built-in auto-memory and claude-mem, on stated facts and continuity | [`stage1/`](stage1/): [`PREREG.md`](stage1/PREREG.md), [`RESULTS.md`](stage1/RESULTS.md) |
| 9: Bench | Against six memory tools, over 12 sessions, when the user forgets to close, and Stage 1's two follow-ups | [`bench/`](bench/): [`PREREG-3.md`](bench/PREREG-3.md), [`RESULTS.md`](bench/RESULTS.md) |
| Stress | `memlayer.py` edge cases, Adopt on other project shapes, `/mimi-close` in adversarial sessions | [`stress/s1/`](stress/s1/), summary in [`../docs/STRESS_TESTS.md`](../docs/STRESS_TESTS.md) |

## Latest results (bench, Sonnet 5.5)

| Track | mimi | Auto-memory | claude-mem | Best other rival | No memory |
|---|---|---|---|---|---|
| Rivals: Stage 1's sqlite-utils sessions | **0.94** | 0.11 | 0.47 | recall 0.56 | — |
| Continuity (F2b), both repos pooled | **0.89** | 0.17 | 0.25 | — | 0.21 |
| Long horizon: 12 sessions, 18 questions | **0.94** | 0.44 | 0.40 | recall 0.61 | 0.21 |
| Long horizon, mimi never closed | 0.43 | | | | |

What these numbers do and don't show is in [`bench/RESULTS.md`](bench/RESULTS.md). In short:
- mimi's lead depends on running `/mimi-close`.
- Tools that record automatically beat mimi on facts the agent read in files.
- The task model changed from Sonnet 5 (Stage 1) to Sonnet 5.5 (bench). On Sonnet 5.5 auto-memory rarely saved
  anything, so its low bench scores don't carry over to Stage 1.

## Known limits of the method

- **Who wrote the tests.** The facts and sessions were written by the author and by Claude, the same model
  family that runs mimi and judges the answers. Facts mentioned in passing, the discovered family and the D0
  arm reduce the home advantage but don't remove it.
- **Small n.** Each family has 1 to 8 questions. Differences under about 0.10 are noise.
- **One judge** in the bench (Sonnet). Earlier experiments used Sonnet and Opus, which agreed on 95–100% of key
  points.
- **Headless sessions.** Real users interrupt, correct and come back days later. The sessions here are scripted.
- **Transcripts on disk.** Claude Code keeps raw session transcripts in `HOME`, and some agents grepped them for
  answers. That helped the other arms, never mimi (see the bench's **Validity**).

## Running the bench yourself

The bench runs in WSL or Linux, one arm at a time, on a Claude subscription token.

1. In the WSL distribution named `Ubuntu`, install Claude Code, Python 3.11, `rsync`, Node.js (claude-mem-lite
   needs 22), Bun and uv. `bench.py` expects Node 22 under `~/.nvm`.
2. Run `claude setup-token` and save the token to `~/bench/.oauth_token`.
3. From PowerShell, run `eval/bench/schedule.ps1`. It registers an hourly task that runs one tick. Each tick
   runs jobs until a usage limit, then stops and resumes on the next tick.
4. Check progress with `python3 eval/bench/bench.py status`. It prints `HALTED:` with a reason when a rival's
   capture stops working. Fix the arm, then delete `~/bench/halt`.

Turn off extra usage on the account, or the bench will run past the 5-hour limit on paid overage until it
sees the overage flag. The per-tool install steps, and the traps each one hit, are in `bench/arms.sh` and in the
deviations section of `bench/PREREG-3.md`.
