# Bench: results

Run 2026-10-03 to 2026-10-04 on a Claude Pro subscription, in WSL, one arm at a time. The questions, arms,
decision rules and validity checks were fixed in [`PREREG-3.md`](PREREG-3.md) before the first result. Every
change made after that is listed there as a deviation, and in **Validity** below.

The mimi under test is v0.1.0 (`046718e`), the version published on GitHub. It was not changed during the run.

## Short answer

- **Against six other memory tools** on Stage 1's sqlite-utils sessions, mimi scored 0.94. The next best were
  recall (0.56) and claude-remember (0.55). mimi beat every rival under the pre-registered rule.
- **Resuming unfinished work (F2b)**, pooled over both repos: mimi 0.89, built-in auto-memory 0.17,
  claude-mem 0.25, no memory 0.21. mimi beat auto-memory by +0.72 (95% interval +0.46 to +0.94).
- **Over 12 sessions (long track)**, mimi scored 0.94 with no wrong claims in 36 answers. Auto-memory scored
  0.44, and the best rival, recall, scored 0.61.
- **mimi's lead depends on running `/mimi-close`.** The same mimi without the close turn (arm D0) scored 0.43,
  a tie with auto-memory (−0.01), and made the most wrong claims of any arm (0.31 per answer).
- **The capture tools win on facts the agent finds in files.** On the discovered family, claude-mem and recall
  scored 0.88 against mimi's 0.75.
- **The model changed since Stage 1.** The `sonnet` alias resolved to Sonnet 5.5, where Stage 1 ran Sonnet 5.
  On Sonnet 5.5, auto-memory rarely chose to save anything. Its scores here are much lower than in Stage 1,
  so the two stages should not be read as one experiment. See **Validity**.

## Setup in brief

| | |
|---|---|
| Task model | `claude -p --model sonnet`, which resolved to `claude-sonnet-5-5`, with `--max-turns 40` |
| Claude Code | 2.1.288 for every session |
| Judge | Sonnet only, with the Stage 1 judge prompt (each key point quoted with evidence before the verdict) |
| Runs per question | 3 (rivals, f2b-sqlite, f2b-cargo), 2 (long) |
| Repos | simonw/sqlite-utils at `6bc1d33`, rust-lang/cargo at `694054f`, the same commits as Stage 1 |
| Isolation | Each arm has its own `HOME` and working copy. Every eval answer starts from the arm's saved post-write state |
| Statistics | Differences are paired by question and run. The interval is a 95% bootstrap over questions (10,000 resamples) |

The arms, tracks and question families are described in [`../README.md`](../README.md) and in
[`PREREG-3.md`](PREREG-3.md).

## Rivals track (sqlite-utils, Stage 1 sessions)

| Arm | Accuracy | Wrong claims per answer | Cost per answer |
|---|---|---|---|
| **D: mimi** | **0.94** | **0.06** | $0.035 |
| N: auto-memory | 0.11 | 0.50 | $0.045 |
| M: claude-mem | 0.47 | 0.33 | $0.060 |
| G: agentmemory | 0.14 | 0.47 | $0.053 |
| R: claude-remember | 0.55 | 0.27 | $0.036 |
| L: claude-mem-lite | 0.37 | 0.47 | $0.061 |
| K: recall | 0.56 | 0.37 | $0.044 |

**Decision rule:** mimi beats X if D − X ≥ 0.15 with an interval excluding 0.

| Rival | D − X | 95% interval | Verdict |
|---|---|---|---|
| claude-mem | +0.46 | +0.09 to +0.81 | mimi beats claude-mem |
| agentmemory | +0.79 | +0.61 to +0.95 | mimi beats agentmemory |
| claude-remember | +0.37 | +0.07 to +0.68 | mimi beats claude-remember |
| claude-mem-lite | +0.56 | +0.29 to +0.83 | mimi beats claude-mem-lite |
| recall | +0.37 | +0.14 to +0.63 | mimi beats recall |

Auto-memory is not a rival under this rule; D − N was +0.82 (+0.62 to +0.98).

On continuity alone (C1, C2), claude-mem (0.92) and recall (0.87) came close to mimi (0.98). The gap was in
stated facts: mimi 0.90, the next best claude-remember at 0.52.

### Follow-up Run 1: the `/mimi-close` scope fix

PREREG-2's Run 1 is judged on this track's D arm. R1 and R4 are the two facts Stage 1's `/mimi-close`
dropped as "about your downstream service".

| Question | Stage 1 D | Bench D | Rule |
|---|---|---|---|
| R1 Lambda, only /tmp writable | 0.00 | 1.00 | must reach ≥ 0.67: **met** |
| R4 vendor CSVs use semicolons | 0.00 | 1.00 | must reach ≥ 0.67: **met** |
| R7 never `--replace` in production | 1.00 | 0.33 | no drop over 0.25: **failed** |
| All other questions | | | no drop over 0.25: met |

**Verdict: Run 1 does not pass as written.** The scope fix works, but R7 regressed. In 2 of 3 runs the agent
answered "technically yes". The rule was stored in `decisions.md`, but the index line for `decisions.md` lists
no headings, while memory files' lines do. The agent read a memory file that matched and stopped there. The
model also changed between the two runs, so part of any difference may be the model.

### Re-run with the index fix (PREREG-4)

`index` now lists `decisions.md`'s headings (commit `4b4ab9c`). [`PREREG-4.md`](PREREG-4.md) re-ran this track's
arm D with that fix on 2026-10-04: same sessions, same 10 questions, 3 runs each, the model pinned to
`claude-sonnet-5-5`, the same judge. Report: `results/rivals-fix/report.txt`.

| Question | Rivals track D | Re-run D | Rule |
|---|---|---|---|
| R7 never `--replace` in production | 0.33 | 1.00 | ≥ 0.67: **met** |
| R1 Lambda, only /tmp writable | 1.00 | 1.00 | ≥ 0.67: **met** |
| R4 vendor CSVs use semicolons | 1.00 | 1.00 | ≥ 0.67: **met** |
| C2 resume the investigation | 1.00 | 0.75 | no drop over 0.25: **met, at the limit** |
| All other questions | 0.96–1.00 | 1.00 | no drop over 0.25: met |

Overall 0.97 with no wrong claims, at $0.034 per answer; the run cost $4.52. **Verdict: with the fix, PREREG-2 Run 1
passes.** C2 dropped by exactly the allowed 0.25. With 3 runs, that is one weaker answer, not a measured
regression.

## Follow-up Run 2: resuming unfinished work (F2b)

Four threads per repo, each left unfinished in a write session and resumed in a fresh one: a plan reversed by
a named person (C3), experiment results and the next step (C4), review feedback with one item done, one left
and one skipped (C5), and a blocked task (C6).

| Arm | sqlite-utils | cargo | Pooled (24 answers) |
|---|---|---|---|
| **D: mimi** | **0.92** | **0.85** | **0.89** |
| N: auto-memory | 0.08 | 0.25 | 0.17 |
| M: claude-mem | 0.25 | 0.25 | 0.25 |
| A: no memory | 0.17 | 0.25 | 0.21 |

| Comparison | sqlite-utils | cargo | Pooled over 8 questions |
|---|---|---|---|
| D − N (primary) | +0.83 [+0.50, +1.00] | +0.60 [+0.19, +0.92] | **+0.72 [+0.46, +0.94]** |
| D − M (secondary) | +0.67 [+0.25, +1.00] | +0.60 [+0.19, +0.92] | **+0.64 [+0.34, +0.89]** |

**Verdict: mimi beats auto-memory on continuity, and beats claude-mem**, under PREREG-2's rule (≥ 0.10 with an
interval excluding 0). Two cautions:
- Auto-memory saved nothing in any of sqlite-utils' four write sessions, and saved in one of cargo's four. That is the
  Sonnet 5.5 effect described under **Validity**. In Stage 1, on Sonnet 5, auto-memory scored 0.80 on
  continuity.
- PREREG-2 asks for D − N pooled over all 12 continuity questions, Stage 1's 4 plus these 8. Because the task
  model changed between the stages, that pooled number would mix two models. It is not reported.

## Long track (sqlite-utils, 12 sessions)

| Arm | All 18 | Stated (8) | Corrected (3) | Discovered (4) | Repo (1) | Continuity (2) | Wrong claims |
|---|---|---|---|---|---|---|---|
| **D: mimi** | **0.94** | **1.00** | **1.00** | 0.75 | 1.00 | **1.00** | **0.00** |
| D0: mimi, never closed | 0.43 | 0.44 | 0.67 | 0.00 | 1.00 | 0.65 | 0.31 |
| N: auto-memory | 0.44 | 0.38 | **1.00** | 0.00 | 1.00 | 0.50 | 0.17 |
| M: claude-mem | 0.40 | 0.00 | 0.50 | **0.88** | 1.00 | 0.60 | 0.17 |
| G: agentmemory | 0.19 | 0.06 | 0.25 | 0.12 | 1.00 | 0.35 | 0.08 |
| R: claude-remember | 0.40 | 0.06 | 0.58 | 0.75 | 1.00 | 0.45 | 0.22 |
| K: recall | 0.61 | 0.38 | 0.75 | **0.88** | 1.00 | 0.65 | 0.14 |
| A: no memory | 0.21 | 0.06 | 0.33 | 0.12 | 1.00 | 0.40 | 0.11 |

**Verdicts under the pre-registered rules:**

1. **Primary, D vs N:** +0.50 [+0.29, +0.72]. *mimi beats auto-memory over the long horizon.*
2. **Secondary:** D − M +0.54 [+0.28, +0.79], D − G +0.75 [+0.59, +0.90], D − R +0.55 [+0.29, +0.77],
   D − K +0.33 [+0.09, +0.55]. mimi beats each of them.
3. **Forgetting to close:** D − D0 = +0.51 [+0.30, +0.73], D0 − N = −0.01 [−0.16, +0.09]. D0 is below
   N + 0.05, so **mimi's lead depends on running `/mimi-close`.** Without it, mimi only holds what the agent
   chose to write during the work, and it is no better than auto-memory.
4. **Discovered facts:** claude-mem and recall scored 0.88, mimi 0.75. That is +0.13 above mimi, under the
   0.15 that PREREG-3 set for a statement, but it is the one family where mimi was not first. mimi missed
   Q15 (a Latin-1 CSV the agent had opened) in both runs.
5. **Corrected facts:** no arm made a wrong claim on them, except D0 (0.33 per answer). Auto-memory and mimi
   both scored 1.00.
6. **Q16, answerable from the code:** every arm scored 1.00. mimi used 2.0 tool calls and about 102k tokens,
   against 2.0 and 94k for auto-memory and 3.0 and 121k for no memory.
7. **Cost:** below.

## Cost

Costs are the `total_cost_usd` that Claude Code reports, an API-equivalent figure. The run itself was billed to
the subscription.

| Track | Write sessions | Eval answers | mimi's Adopt build | Total |
|---|---|---|---|---|
| rivals | $11.35 (38 sessions, with re-runs) | $10.15 (214) | — | $21.50 |
| f2b-sqlite | $4.46 (16) | $2.31 (48) | $0.53 | $7.30 |
| long | $20.44 (96) | $13.37 (288) | $0.75 | $34.56 |
| f2b-cargo | $4.28 (16) | $2.13 (48) | $0.57 | $6.98 |
| **All** | | | | **$70.34** |

Judge calls are not included.

**Write-phase cost per arm, long track (12 sessions):** mimi $5.15 (it adds a `/mimi-close` turn to each
session), claude-mem $2.67, D0 $2.60, recall $2.17, agentmemory $2.09, auto-memory $1.98, claude-remember
$1.91, no memory $1.87.

**Cost per answer** stays the lowest or near it for mimi on every track ($0.035–0.043), because the agent finds
the answer in memory and stops.

## Validity

**The task model changed between Stage 1 and the bench.** Stage 1's sessions report `claude-sonnet-5`. Every bench
session reports `claude-sonnet-5-5`, because the `sonnet` alias moved. PREREG-3 names the model as "Sonnet" and
did not record this as a deviation. The effect is largest on auto-memory, which depends on the model choosing
to save:

| Track | Write sessions where auto-memory saved anything |
|---|---|
| rivals (same sessions as Stage 1, where it saved 7 files) | 0 of 5 |
| f2b-sqlite | 0 of 4 |
| long | 5 of 12 |
| f2b-cargo | 1 of 4 |

Within the bench, every arm ran on the same model, so the comparisons between arms hold. Comparisons with Stage 1
do not.

**Some answers read raw session transcripts.** Claude Code keeps every session's transcript under
`HOME/.claude/projects/`, and the eval snapshot keeps them. In 30 of 598 answers, an agent grepped those
transcripts for the answer: no memory (A) 14 times, agentmemory 9, auto-memory 6, recall 1. mimi never did. This
can only raise the other arms' scores, so mimi's leads are, if anything, understated. The runner now
deletes the transcripts before the eval snapshot, so a future run is free of this.

**Capture checks halted the long track three times, all false alarms.** PREREG-3 checks that each rival's store
holds something after a track's first session. The long track's first session is read-only, and three tools
correctly chose to store nothing from it:
- claude-mem's observer skipped every event (`skip_summary`).
- agentmemory stored observations, but in keyless mode they carry no repo path, which the check looked for.
- claude-remember's Haiku call answered `SKIP`.

Each check now tests that the tool's pipeline ran, not that it stored something (commits `13c2f04`, `f9c6470`,
`bca4ebb`). The halted sessions were restored from their snapshots and re-run, so no result comes from a broken
state.

**agentmemory's engine download failed on its long-track install.** It ran its first session without its engine.
A copy of the engine from the rivals install was put in place, the session was re-run, and the arm now refuses
to start without the engine. agentmemory ran in its default keyless mode throughout, which probably explains its
low scores.

**The bench account ran past its 5-hour limit on paid overage.** The account had extra usage turned on, so
Claude kept answering instead of refusing: about 170 jobs ran past the limit. The answers are unaffected. The bench now
pauses when a call reports overage.

**Other limits:**
- One judge, Sonnet. On mimi's 34 rivals answers, Sonnet and Opus agreed on every key point.
- Small n. The F2b intervals rest on 4 questions per repo, and each long-track family has 1 to 8 questions.
- The long track's facts and sessions were written by Claude, the same model family as mimi's author and the
  judges. The discovered family and the D0 arm are there to test mimi where it should be weak.
- Answers and memory dumps contain the bench machine's paths (`/home/aryaman/bench/...`).

## Files

| Path | Contents |
|---|---|
| `PREREG-3.md` | Questions, arms, decision rules and deviations, written before the run |
| `bench.py`, `arms.sh`, `plan.json` | The job runner, the per-tool adapter and the track plan |
| `schedule.ps1`, `tick.sh` | The hourly Windows task that runs one tick in WSL |
| `tracks/long/` | The long track's 12 sessions and 18 questions |
| `results/<track>/report.txt` | The full report: every family, every comparison, every question |
| `results/<track>/answers.jsonl` | Every answer with its score, wrong claims, tokens, tools and cost |
| `results/<track>/memory_<arm>.txt` | Each arm's memory after its last write session |
