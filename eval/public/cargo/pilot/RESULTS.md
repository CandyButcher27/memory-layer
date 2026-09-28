# Pilot: mimi vs claude-mem vs claude-mem-lite on rust-lang/cargo

Run on 2026-09-28 on one GitHub Codespace (4 vCPU, 16 GB). This is a pilot: one repository, five facts,
three runs per question. Its purpose was to check that the method works and to see whether the gap is
large enough to justify a full run.

## Setup

- **Repo:** rust-lang/cargo pinned at `694054f34bcb04025b16d0eaf075038c0e58a15d`, the same SHA and the
  same `sessions.json` / `recall.json` as the earlier public-repo run (`../RESULTS.md`).
- **Arms:**
  - **D, mimi:** built by Adopt (Opus). The five work sessions follow the project's `CLAUDE.md`.
  - **M, claude-mem 13.28.0:** installed with `npx claude-mem install --provider claude`. It compresses
    with its default model, `claude-haiku-4-5-20251001`.
  - **L, claude-mem-lite 6.19.0:** installed with `node install.mjs install`, with no API key, so any
    background model call goes through `claude -p`.
- **Isolation:** each arm ran with its own `HOME`, so plugins, hooks, MCP servers and data directories
  could not leak between arms. Claude Code's own auto-memory was off in every arm
  (`CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`), so each arm tested only its tool.
- **Tools:** the task model could use each arm's memory tools: `Skill` in every arm, plus
  `mcp__plugin_claude-mem_mcp-search` in M and `mcp__mem-lite` in L.
- **Protocol:** 5 write sessions per arm (Sonnet), then a drain (wait until no arm wrote anything for
  3 minutes), then 5 recall questions × 3 runs in fresh `claude -p` sessions (Sonnet). Two judges,
  Sonnet and Opus.
- **Token accounting:**
  - Every arm's Claude Code talked to its own logging proxy (`eval/harness/proxy.py`).
  - claude-mem's worker removes `ANTHROPIC_BASE_URL` before it spawns its SDK subprocess, so it bypasses
    the proxy. Its usage was read from its own debug log (`Token usage captured` lines, de-duplicated).
  - Check on the method: for D, the proxy total equals the main-session total exactly, so nothing was
    missed and nothing counted twice. For L, the proxy total also equals the main sessions, which means
    claude-mem-lite made no background model calls in this run.

## Recall (15 answers per arm, mean of both judges)

| | mimi | claude-mem | claude-mem-lite |
|---|---|---|---|
| Accuracy, Sonnet / Opus judge | **1.00 / 1.00** | 0.17 / 0.23 | 0.47 / 0.43 |
| Wrong claims per answer (Sonnet judge) | **0.00** | 0.67 | 0.73 |
| Tool calls / searches per answer | **1.13 / 0.00** | 5.27 / 2.00 | 4.47 / 1.53 |
| Context tokens per answer (task model) | **73.5k** | 178.6k | 206.1k |
| Cost per answer (task model) | **$0.035** | $0.089 | $0.097 |
| Background tokens during recall | 0 | 617k Haiku (worker processing the recall sessions) | 0 |
| Time per answer | **10.8 s** | 20.9 s | 22.7 s |

Per question (Sonnet judge):

| Question | mimi | claude-mem | claude-mem-lite |
|---|---|---|---|
| R1 mirror 429s carry no Retry-After | 1.00 | 0.00 | 0.17 |
| R2 corrected rate limit (120, not 60) | 1.00 | 0.17 | 0.50 |
| R3 keep net.retry at 3, and why | 1.00 | 0.33 | 0.67 |
| R4 release build time, 6m41s median of 5 | 1.00 | 0.00 | 0.00 |
| R5 Defender locks new .exe files | 1.00 | 0.33 | 1.00 |

## Write cost (5 sessions per arm, plus setup)

| | mimi | claude-mem | claude-mem-lite |
|---|---|---|---|
| Setup | $0.49 (Adopt, Opus, 10 turns) | none | none |
| Work sessions (task model) | $1.22 | $1.20 | $0.96 |
| Context tokens, work sessions | 2.92M | 3.15M | 1.94M |
| Background model calls, sessions + drain | 0 | 69 calls, 1.29M context tokens (Haiku) | 0 |
| What was stored | +31/−4 lines across `decisions.md`, `memory/build.md`, `memory/external.md` | 19 observations | 5 observations, all from `mem_save` calls the task model made, plus a `CLAUDE.md` block |

claude-mem's worker, over the whole run, came to 1.9M Haiku context tokens across 117 calls. Its
debug log understates output tokens: the two worker sessions that saved a `cost-state` record show about
1,450 output and 1,240 thinking tokens per session. The worker cost is roughly $0.4–0.6, small next to
the task model.

## Why claude-mem scored low

claude-mem stored most of the facts. Its database contains the missing Retry-After, 60 and 120 req/min,
6m41s, and the Defender lock. It lost only the reason behind the net.retry decision (the hidden
40-minute outage). But its session-start injection is a list of observation titles, and those titles
describe code, not what people said:

```
2 ○ Cargo uses exponential backoff with 10-second max when Retry-After header missing
18 ○ No hardcoded per-minute rate limit values found in codebase
```

The details sit behind `get_observations` and the `mem-search` skill. In 15 recall runs the task model
never called either one. It grepped the repository instead, found nothing about the mirror, and answered
from the code. The title "No hardcoded per-minute rate limit values found" led it to state there was no
known limit.

claude-mem-lite scored where the task model had saved a fact itself with `mem_save` during the write
session (R5, and partly R2 and R3). It kept no LLM summaries of what was said, so R4 (the timing) was
lost in every run.

## Spend

| Item | Cost |
|---|---|
| Task-model runs (build, sessions, recall), all arms | $7.19 |
| Two discarded claude-mem S1 attempts (see below) | $0.80 |
| Judges (90 verdicts), probes, claude-mem worker | ~$4, estimated |
| **Total** | **~$12** |

## What went wrong, and how it was handled

- **claude-mem's first session recorded nothing.** Its hooks did not reach the worker in the first
  `claude -p` session after install. It worked in a probe run, so the arm was reset (fresh database, fresh
  copy of the repo) and S1 re-run. The failed attempts' tokens are excluded from the tables.
- **claude-mem's worker transcripts are mostly not saved,** so the first accounting method, SDK
  transcripts, undercounted it. The arm was reset once more with `CLAUDE_MEM_LOG_LEVEL=DEBUG` and counted
  from its log.
- **Drain did not watch claude-mem's log directory.** All 19 write-phase observations have timestamps
  before recall began, so recall did not start early.

## Limits of this pilot

- **Home advantage.** The recall facts, the one-minute rule and this protocol all come from mimi's own
  evaluation. The questions test facts a person stated, which is exactly what mimi is built to keep.
  Continuity of work in progress ("what did we try last session") is where automatic capture should do
  better, and it was not tested.
- **Small sample:** one repository, 5 facts, 3 runs each.
- **Headless only.** A person using claude-mem interactively can ask it to search memory. Here the agent
  had to decide that by itself.
- **Prompt cache:** all arms share one account, so the split between cache writes and reads depends on
  run order. The tables therefore report total context tokens.
