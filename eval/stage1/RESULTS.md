# Stage 1 results

Run on 2026-09-28 against the criteria in [`PREREG.md`](PREREG.md), which was committed before any run
(`6a4a11d`).

> **Follow-up, run 2026-10-03 to 2026-10-04 in the bench.** The `/mimi-close` scope bug described below is
> fixed in `3bdb281`. PREREG-2's re-run and its 8 more continuity questions (F2b) ran as part of the bench:
> results in [`../bench/RESULTS.md`](../bench/RESULTS.md). The bench ran on Sonnet 5.5, where this stage ran on
> Sonnet 5, so its numbers are not pooled with the ones below.

- **Repos:** rust-lang/cargo and simonw/sqlite-utils.
- **Arms:**
  - A: no memory
  - N: Claude Code's built-in auto-memory
  - D: mimi
  - M: claude-mem 13.28.0
- **Models:** Sonnet was the task model. Sonnet and Opus judged separately.
- **Volume:** 272 answers per judge, and every one received a verdict.

## Headline

| | A: none | N: auto-memory | D: mimi | M: claude-mem |
|---|---|---|---|---|
| **F1 stated facts**, accuracy (48 answers) | 0.09 | 0.51 | **0.83** | 0.15 |
| F1 wrong claims per answer | 0.77 | 0.21 | **0.02** | 0.56 |
| **F2 continuity**, accuracy (20 answers) | 0.39 | 0.80 | **0.97** | 0.42 |
| F2 wrong claims per answer | **0.10** | 0.55 | 0.25 | 0.30 |
| Context tokens per answer, F1 / F2 | 160k / 171k | 84k / 125k | **63k / 69k** | 170k / 201k |
| Cost per answer, F1 / F2 | $0.062 / $0.071 | $0.036 / $0.044 | **$0.029 / $0.029** | $0.077 / $0.094 |

Paired differences, bootstrap over questions (95% interval):

| | F1 | F2 |
|---|---|---|
| D − M | **+0.68** [+0.41, +0.88] | **+0.55** [+0.21, +0.89] |
| D − N | **+0.32** [+0.10, +0.55] | **+0.17** [+0.02, +0.33] |
| M − N | −0.36 [−0.60, −0.10] | −0.38 [−0.59, −0.10] |

F2 has only 4 distinct questions, so its intervals come from resampling 4 items. They are coarse.

## The pre-registered decision rules

1. **F1:** D − M = +0.68 and D − N = +0.32, both ≥ 0.15 with intervals excluding 0. **mimi keeps its
   advantage.**
2. **F2:** D − M = +0.55, interval excluding 0. **mimi wins continuity.** Only 4 questions, and the
   lower bound against N is +0.02.
3. **Built-in default:** N is below D − 0.10 in both families (0.51 vs 0.83, 0.80 vs 0.97), so mimi shows
   value over Claude Code's default. On F2 the margin is small.
4. **Cost:**
   - mimi is the cheapest per answer.
   - It costs more to write, because every session ends with a `/mimi-close` turn at about $0.48 each
     ($2.43 on cargo, $2.42 on sqlite-utils, over 5 sessions each).
   - claude-mem's writing runs in a background Haiku worker, which also processes every eval session:
     107 write calls and 198 eval calls in total.

## Per question (mean of both judges; A / N / D / M)

| Repo | Q | What | A | N | D | M |
|---|---|---|---|---|---|---|
| cargo | R1 | crates.io block, corrected to July | 0.00 | 0.25 | 1.00 | 0.00 |
| cargo | R2 | mirror prunes yanked crates Sundays | 0.25 | 0.17 | 1.00 | 0.33 |
| cargo | R3 | Priya owns MSRV | 0.00 | 0.00 | 1.00 | 0.00 |
| cargo | R4 | 23 min test run | 0.00 | 0.00 | 1.00 | 0.08 |
| cargo | R5 | sccache 50 GB | 0.00 | 0.08 | 1.00 | 0.00 |
| cargo | R6 | no build-std (cache 40→80 GB) | 0.33 | 1.00 | 0.92 | 0.42 |
| cargo | R7 | rebase before 2026-10-15 | 0.00 | 1.00 | 1.00 | 0.00 |
| cargo | R8 | resolver needs platform reviewer | 0.00 | 1.00 | 1.00 | 0.00 |
| sqlite-utils | R1 | Lambda, only /tmp writable | 0.00 | 0.33 | **0.00** | 0.00 |
| sqlite-utils | R2 | insert time, corrected to 6m10s | 0.08 | 0.25 | 1.00 | 0.17 |
| sqlite-utils | R3 | reporting stays on 3.x | 0.00 | 1.00 | 0.83 | 0.00 |
| sqlite-utils | R4 | vendor CSVs use semicolons | 0.50 | 0.08 | **0.00** | 0.83 |
| sqlite-utils | R5 | Dmitri owns the geo plugin | 0.00 | 0.00 | 0.50 | 0.00 |
| sqlite-utils | R6 | schema freeze 2026-11-01 | 0.00 | 1.00 | 1.00 | 0.00 |
| sqlite-utils | R7 | never --replace in prod | 0.25 | 1.00 | 1.00 | 0.25 |
| sqlite-utils | R8 | no SpatiaLite in prod | 0.00 | 1.00 | 1.00 | 0.33 |
| cargo | C1 | resume the feature | 0.78 | 1.00 | 1.00 | 0.58 |
| cargo | C2 | resume the investigation | 0.00 | 0.68 | 1.00 | 0.03 |
| sqlite-utils | C1 | resume the feature | 0.72 | 0.96 | 1.00 | 0.98 |
| sqlite-utils | C2 | resume the investigation | 0.07 | 0.57 | 0.90 | 0.10 |

## What explains the gaps

- **claude-mem stored code, not conversation.** It kept 8 observations on cargo and 14 on sqlite-utils,
  nearly all of them descriptions of code the agent had read. It processed the cargo investigation
  session (T2) in over 10 batches and stored nothing, logging `skip_summary reason="routine code
  navigation"`. The user's ruled-out hypotheses went with it, so it scored 0.03 and 0.10 on resuming the
  investigations.
  - It did well only where the working tree carries the state (sqlite-utils C1, 0.98, where the diff
    shows step 1).
  - It did well once where a fact happened to become an observation (sqlite-utils R4, 0.83).
  - Its context was injected in every run, and the agent called its MCP tools, so this is not a setup
    failure.
- **Built-in auto-memory is a real baseline.** It saved 7 topic files per repo and got every decision,
  deadline and review rule. It missed measurements, people and infrastructure details, and on F2 it made
  the most wrong claims (0.55 per answer).
- **mimi's misses are its own filter.** On sqlite-utils, `/mimi-close` saw the Lambda `/tmp` fact and the
  semicolon-CSV trap. It dropped both as "about your downstream ingest service, not this project's own
  code". Dmitri was stored, but half the answers still missed him. The one-minute test is right, but the close command also applies a
  "does this belong to this repo" judgment that the rules never asked for. This needs a fix.
  - When mimi had nothing, it said so rather than guessing: 0.02 wrong claims per answer on F1.

## Validity checks and deviations

- **A, cargo, T2, turn 1** hit the 40-turn cap (`error_max_turns`). The user's second turn still ran. By
  the pre-registered rule, arm A is invalid for cargo. A is the control, and its cargo numbers are left
  in the tables marked by this note.
- **M, cargo, T2** produced no observation, so the rule "every write session produced at least one
  observation" fails as written. The log shows the capture pipeline worked and claude-mem chose to store
  nothing. **Deviation:** M is reported, not excluded, because excluding it would hide the behaviour
  being tested.
- **N** wrote 7 auto-memory files on each repo. Every arm had step 1 of T1 in its working tree.
- **Harness fixes during the run, none of which changed any answer:**
  - claude-mem's npx installer leaves a marketplace Claude Code cannot load ("cache-miss"). It was
    re-registered with `claude plugin marketplace add` before any session, and capture was verified.
  - The first snapshot filled the disk (agents in A and M built cargo). Snapshots moved to `/tmp`, and
    `/target/` and tool runtimes were excluded from them.
  - The judge's verdict regex broke on one reply containing two JSON blocks. It now takes the last
    verdict line, and the 177 verdicts already written were kept.

## Spend

| Item | Cost |
|---|---|
| Write sessions, all arms, both repos (includes `/mimi-close` turns) | $24.7 |
| mimi Adopt builds (Opus) | $1.05 |
| Eval answers (272) | ~$14.6 |
| Judges (544 verdicts), claude-mem worker, warm-ups | ~$10, estimated |
| **Total** | **~$50** |

## Limits

- I wrote the facts and sessions. The facts now come up in passing, and F2 favours automatic capture,
  but some home advantage remains.
- There are 2 repos and 16 F1 questions, but only 4 F2 questions.
- Runs are headless. Judges are from the same model family as the task model.
