# Evaluation

Eight experiments, a stress-test suite, and every failure fixed and re-tested. Experiments 1–7 ran before the
rename, so they call mimi "the memory layer" or "this layer", and its close command `/session-close`.

**Short answer:**
- **Keeping what people say:** on five large public repositories, mimi's recall was 0.79 against 0.29 for a
  conventional notes setup, at about half the cost per answer.
- **Against Claude Code's built-in auto-memory and claude-mem:** mimi led on stated facts (0.83 vs 0.51 and
  0.15) and on resuming unfinished work (0.97 vs 0.80 and 0.42). See Experiment 8.
- **Finding past incidents:** mimi is no better, and slightly worse, than plain `git log --grep` in repositories
  whose commit history already explains them (0.76 against 0.81).

---

## Experiments 1–6: one private production project

These ran on a private production codebase: 171 commits, 48 of them `fix:` commits, with a conventional
memory setup (about 4,600 lines built up over months) already in use. The code, tasks, answer keys and
transcripts stay private. This section publishes only the method and the aggregate numbers.

**Arms:**
- no memory
- the existing conventional setup (a `memory/<component>.md` knowledge base plus `CLAUDE.md`)
- mimi, built by Adopt from the conventional setup's content: 744 lines
- mimi plus the generated `index`

**Method:**
- Every task ran in a fresh headless `claude -p` session on a Codespace. Tasks used Sonnet 5, and Experiment
  6 re-ran on Opus 5.5.
- Retrieval questions were written from commit messages, diffs and code before any memory existed. Recall
  questions used facts invented for the test and given in session prompts.
- A blind judge graded every answer against the key. Experiment 6 re-graded with Sonnet and Opus
  separately.

| # | What | Result |
|---|---|---|
| 1 | Retrieval, 12 past-incident tasks × 2 | No memory 0.86, conventional 0.93, mimi 0.88 |
| 2 | The same tasks with `index` | mimi 0.93. The miss in Experiment 1 was a fact mimi held but whose index line never mentioned it |
| 3 | 6 write sessions, then recall of their facts | Both 0.97. mimi wrote +83 lines against +208 and was cheaper to read back: 3.0 vs 4.4 tool calls, $0.06 vs $0.08 per answer, 0.07 vs 0.20 wrong claims |
| 4 | `/session-close` smoke test | Routed a new fact and a correction correctly, asked about unsourced numbers, and wrote nothing on a second run with nothing new. About $0.70 per close |
| 5 | Handoff, with and without a `## Last session` section, 3 runs each | Both resumed the right task. With the section, the dead end a user mentioned was recorded 3 of 3 times; without it, 1 of 3, and one run reopened a settled decision |
| 6 | Opus re-runs, two judges | Retrieval 0.99 vs 1.00 (both at the ceiling). mimi still wrote about half as much memory, and recall cost about 27% less. Judges agreed on 95–100% of key points |

---

## Experiment 7: five famous public repositories

**Question:** does the result hold beyond one client project, on large repositories with long, well-written
histories?

**Method:** `eval/public/PROTOCOL.md`, run once per repo by five parallel agents, each on its own Codespace.
Each repo's full report is `eval/public/<repo>/RESULTS.md`.
- Pinned HEAD, with any agent-instruction files stripped so every arm starts equal.
- 10 retrieval tasks written from raw git before any memory existed: 4 recurring bugs, 3 reverted
  decisions, 2 platform quirks, 1 code question.
- Three arms: A no memory, B the current setup (built by `/harness`), D this layer (built by Adopt).
  Both memory arms were built by Opus.
- Sonnet as the task model, 2 reps per task.
- The write and recall test with 5 facts only a person could know. The last session corrects an
  earlier fact.
- Graded by a Sonnet judge and an Opus judge separately.

| Repo | Language | Commits | Memory built (B / D lines) |
|---|---|---|---|
| git/git | C | 82,306 | 220 / 114 |
| django/django | Python | 34,949 | 276 / 85 |
| rust-lang/cargo | Rust | 23,301 | 316 / 94 |
| nodejs/node | JS/C++ | 48,620 | 371 / 163 |
| golang/go | Go | 67,724 | 286 / 101 |

**Retrieval, past incidents (mean of both judges):**

| Repo | A: none | B: current | D: this layer |
|---|---|---|---|
| git | 0.77 | **0.80** | 0.63 |
| django | **0.82** | **0.82** | 0.73 |
| cargo | **0.83** | 0.74 | 0.74 |
| node | 0.80 | 0.86 | **0.90** |
| go | 0.81 | 0.81 | 0.80 |
| **Mean** | **0.81** | **0.81** | 0.76 |

**Recall of facts people stated in sessions (mean of both judges):**

| Repo | B's copy: current | D's copy: this layer | Cost per answer (current / layer) |
|---|---|---|---|
| git | 0.32 | **0.72** | $0.09 / $0.03 |
| django | 0.33 | **0.44** | $0.05 / $0.05 |
| cargo | 0.15 | **1.00** | $0.06 / $0.03 |
| node | 0.37 | **0.80** | $0.08 / $0.03 |
| go | 0.28 | **1.00** | $0.06 / $0.03 |
| **Mean** | 0.29 | **0.79** | $0.07 / $0.03 |

The judges disagreed on 0–7% of key points per repo.

**What it shows:**
- **Recall is where the layer earns its place.** It won on all five repos, by +0.50 on average, at about
  half the cost per answer and with far fewer wrong claims.
  - The current setup mostly wrote descriptions of code the agent had just looked up. It dropped what
    people said: CI facts, decision reasons, timings, traps.
  - When a fact was missing, the current setup filled the gap with a plausible value from the repo. On
    node, all 3 runs gave the AIX version from `BUILDING.md` instead of the one the user had stated.
  - Both setups handled corrections in place where they had stored the fact.
- **Retrieval of past incidents doesn't need memory on well-documented repos.** Across the five repos,
  having no memory tied the current setup (0.81 each). Their commit messages already are the memory, and
  `git log --grep` finds the answer.
- **This layer lost retrieval (0.76) on 4 of 5 repos.**
  - Adopt keeps very little from a repo with no prior notes: 85–163 lines, often an empty
    `decisions.md`.
  - The index still sends the agent to those files first. The agent reads them, finds nothing, and
    sometimes treats "not recorded" as "no answer": git T09, go T05.
  - On node, where Adopt recorded 9 real past incidents, the same design scored best of the three
    (0.90).
- **The layer repeated two failures on several repos.**
  - It treated a measurement the user reported as "derivable from the code" and dropped it (git,
    django, node). The one-minute test was applied to the whole message, not to each fact.
  - Sessions left two `Last verified:` lines in a file, because they don't run `check` until clean
    (cargo, node).

**Fixes this points to (applied 2026-09-24; not yet re-evaluated on these repos):**
1. A memory miss is not an answer. When memory has nothing on the question, fall back to
   `git log --grep` and the code before concluding.
2. Don't route the agent to empty memory files first. Leave an empty `decisions.md` or `ISSUES.md` out
   of the index, or mark it as empty.
3. Apply the one-minute test per fact. A number, date or decision a person states is never "derivable
   from the code".
4. Write sessions must run `check` until clean, like `/session-close` does.

Where each fix went:
- **Fix 1** is a line in the `CLAUDE.md` block, which loads into every session.
- **Fix 2** is code: `index` now marks a memory file, `ISSUES.md` or `decisions.md` that holds nothing
  as `— empty`. `init` runs `index` at the end, so a fresh block starts marked, and `check` flags a
  marker that has gone stale. A new stress test covers it.
- **Fix 3** is a rule in the block, in `/session-close` step 2 and in Adopt, with the Oracle example.
- **Fix 4** is a rule in the block: after any memory edit, run `index`, then `check`, until clean.

Only a rerun of the D and F arms on these repos will show whether retrieval recovers.

**Spend:** about $87 across the five repos (git $22, django $15, cargo $14, node $18, go $18).
Two interruptions:
- The account's 2-running-Codespace limit serialised the runs.
- A network drop and a process restart stopped three agents. They resumed with their earlier task
  files unchanged.

---

## Experiment 8: Stage 1, against built-in auto-memory and claude-mem

This experiment ran after the rename, so it calls the layer mimi and its close command `/mimi-close`. It
has its own documents:
- the design and decision rules, committed before the run: `eval/stage1/PREREG.md`
- the full results, validity checks and deviations: `eval/stage1/RESULTS.md`
- a single-repo pilot that came first: `eval/public/cargo/pilot/RESULTS.md`

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
- **Judging:** Sonnet and Opus grade every answer against a key written before any memory existed. Each
  judge quotes the evidence for each key point before its verdict.

| | No memory | Auto-memory | claude-mem | mimi |
|---|---|---|---|---|
| Stated facts, accuracy | 0.09 | 0.51 | 0.15 | **0.83** |
| Stated facts, wrong claims per answer | 0.77 | 0.21 | 0.56 | **0.02** |
| Continuity, accuracy | 0.39 | 0.80 | 0.42 | **0.97** |
| Context tokens per answer | 160–171k | 84–125k | 170–201k | **63–69k** |
| Cost per answer | $0.06–0.07 | $0.04 | $0.08–0.09 | **$0.03** |

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

Two follow-ups are pre-registered in `eval/stage1/PREREG-2.md` and have not run: a re-run after the
`/mimi-close` scope fix (`3bdb281`), and 8 more continuity questions. Stage 1 cost about $50.

---

## Stress tests

The suite and its pass conditions are in `STRESS_TESTS.md`. The S1 report is in `eval/stress/s1/RESULTS.md`.
S2 and S3 ran on private repositories, so only this summary of them is published. Three subagents ran it in parallel on scratch copies. The real repos
were verified untouched afterwards.

| Area | What it tested | Result | Cost |
|---|---|---|---|
| S1 | `memlayer.py` edge cases, 28 pytest cases | 16 pass, 12 fail | $0 |
| S2 | Adopt on 4 other project shapes, plus a rerun | 4 pass, 1 partial; 28 facts checked, none false | $5.39 |
| S3 | `/session-close` in 9 adversarial sessions | 7 pass, 1 partial, 1 fail | $9.84 |
| S4 | Design limits (merge conflicts, context size, heading renames) | measured | $0 |

**Held up:**
- Secrets and a third party's private detail pasted into a session never reached any file.
- Bugs went to `ISSUES.md` with the exact symptom, fix commit and test.
- A reversed decision got a new DEC entry, and the old one was marked superseded with its reasoning
  intact.
- A silent contradiction was raised as a question, not overwritten.
- A typo-only session wrote nothing.
- A project without the layer made `/session-close` stop without creating files.
- Adopt worked on a repo with no memory, on a repo with the old harness (1,401 → 468 lines, every
  "DO NOT UNDO" rule kept), on a tiny repo and on a C repo. A second Adopt run changed 2 lines.

**Broke, then fixed and re-tested (2026-09-24):**

| Finding | Fix | Re-test |
|---|---|---|
| `check` crashed with `UnicodeEncodeError` on a Windows pipe | stdout reconfigured to UTF-8 | S1.13b passes |
| Invalid date gave a traceback; future or duplicate dates passed | Dates parsed with errors reported; future and duplicate dates flagged | S1.09 (3 cases) pass |
| `index` rewrote index-shaped prose outside the block | Index updates scoped to the managed block | S1.08 passes |
| Files with spaces or in subfolders silently skipped | Index lines accept any file name; subfolders indexed and noted | S1.05, S1.06 pass |
| A `#` line inside an issue's code block split the entry | Fenced code stripped before splitting | S1.10 passes |
| Read-only file or non-UTF-8 file gave a traceback; `init` on a mistyped path created it | One-line error and exit 1; the target must be an existing directory | S1.12, S1.12b pass |
| LF files rewritten to CRLF on Windows | Each file keeps its own line endings | S1.02 (both variants) pass |
| A memory path inside a heading raised a false "missing file" | Paths taken only from index lines | S1.04b passes |
| Conflict markers passed `check` | Flagged in every layer file | New S4.1 test passes |
| No limit on the auto-loaded context | `check` flags `CLAUDE.md` + `STATE.md` over 16 KB (the adopted production-project layer is 9.8 KB) | New S4.2 test passes |
| Renamed headings left a stale index while `check` said clean | `check` flags stale index lines | New S4.3 test passes |
| Machine-specific absolute path written into `CLAUDE.md` | Written as `"$HOME/..."`, confirmed working in Git Bash and PowerShell | New path test passes; Adopt rerun wrote `$HOME` |
| `/session-close` wrote `Uncommitted:` before `index` changed `CLAUDE.md` (S3.9) | `index` runs before `STATE.md` is written | S3.9 rerun: second close changed nothing ($0.95) |
| `STATE.md` repeated facts held in `memory/` (S3.6) | `STATE.md` references facts by file; `Tried, failed` only for things tried | S3.6 rerun: each of 5 facts in one memory file; `STATE.md` points to them by file, and `Uncommitted:` now includes `CLAUDE.md` ($0.84) |
| Close edited memory from an inference (S3.1) | Inferences go to Questions, not memory | S3.1 rerun: no secret in any file, and `memory/external.md` untouched ($0.64) |
| `STATE.md` header comment dropped | Keep-the-header rule in step 5 | Not separately re-tested |
| Adopt deleted 23 tracked `.docs/` files and edited `README`/`CONTRIBUTING` (S2.1) | `SKILL.md` limits deletion to agent-memory files; project docs are never deleted or edited | S2.1 rerun on a fresh clone, same prompt: 0 tracked files deleted or modified, 28/28 docs kept, `check` clean, 133 lines ($1.29) |
| `Last verified:` reset without re-testing; a sandbox quirk recorded as a project trap; half-ignored layer files | `SKILL.md` Adopt rules for each | Not separately re-tested |

The S1 suite now has 34 cases (the 28 original, 4 for the S4 findings, and later additions), and all pass as of 2026-09-29:
`uv run --no-project --with pytest pytest eval/stress/s1`. S1.04b changed on purpose. Checking before
`index` now correctly reports a stale index, and the test's real subject, no false missing-file report,
still holds after `index`.

**Still open:**
- **Parallel sessions:** two sessions that each close on separate branches still conflict in
  `STATE.md`. `check` now catches leftover markers, but the conflict itself is inherent to a single
  current-state file.
- **One project:** the model-driven results still come from one project, plus four for Adopt.

---

## Conclusions

1. **Accuracy is the same.** With `index`, the new layer matches the current setup on retrieval (0.93
   vs 0.93) and on recall of newly written facts (0.97 vs 0.97).
2. **It writes much less.** 744 lines against about 4,600 after Adopt, and about 40% as many lines
   written in the same sessions, with each fact landing in fewer files.
3. **Reading memory back is cheaper.** In recall, the new layer used 32% fewer tool calls, 59% fewer
   searches, 19% fewer input tokens and 25% less cost per answer, with fewer wrong claims.
4. **The `index` command is essential.** Without it the new layer lost a fact it already held. A prose
   rule could not get agents to write symptom-oriented index lines. Generating them from headings did.
5. **`/session-close` works on a smoke test.** It routed a new fact and a correction correctly,
   asked about numbers with no source instead of guessing, and wrote nothing when there was nothing
   new, at about $0.70 per close.
6. **It holds on Opus, with two judges.** On Opus 5.5 both setups hit the retrieval ceiling
   (0.99 against 1.00). The new layer still writes about half as much memory, and recall costs about
   27% less. Sonnet and Opus judges agree on 95–100% of key points (Experiment 6).
7. **On five large public repos, recall is the win and retrieval the weak spot.** Recall 0.79 against
   0.29, winning on all five repos. Retrieval 0.76 against 0.81 for both the current setup and no
   memory, because a thin adopted memory sends the agent to empty files first (Experiment 7).
8. **Handoff belongs in `STATE.md`, not a new file.** Both setups resumed the right task at the right
   step. The `## Last session` section's `Tried, failed:` line is what kept a dead end from being
   reopened (Experiment 5).
9. **Having no memory is only slightly worse on this project** (0.86), because its commits and code
   comments are unusually detailed. Expect a bigger gap on projects with thin commits.

## Limits

- Experiments 1–6 cover one project. Experiment 7 adds five public repos, but only for retrieval and recall, with 20 and 15 answers per arm per repo. There are 24 answers per arm in Experiments 1 and 2, and 15 in Experiment 3, so
  accuracy differences under about 0.1 are noise.
- Experiments 1–3 ran on Sonnet 5, and 4–5 on Opus 5.5 (see **Models**). Experiment 6 reran the
  retrieval and write tests on Opus: same conclusions, but retrieval hit the ceiling on Opus, so it no
  longer separates the setups.
- The judge prompt changed during Experiment 5 (see there). Experiments 1–3 kept their original
  verdicts.
- A single Sonnet judge. It sometimes counted real but unverifiable details (issue IDs, line numbers) as
  wrong claims, which inflates the wrong-claim counts for B and C.
- Some answer keys are debatable: one task's wording was ambiguous, and in another the judge penalised
  correct "already fixed at HEAD" answers.
- Arm A could still read old memory files through git history. It did so once.
- Experiment 3 used invented facts and only 6 sessions. Drift over months of real use is not tested.
- Costs are the `total_cost_usd` figures Claude Code reports. The runs themselves were billed to the
  Claude plan.

Open limitations of mimi as it ships today:

- **Retrieval:** on public repositories it was slightly worse than no memory (0.76 against 0.81). The
  fixes for that are applied but not yet re-measured.
- **Continuity:** the lead over built-in auto-memory rests on 4 questions, with a lower bound of +0.02.
  Eight more are pre-registered and have not run.
- **The `/mimi-close` scope fix is not re-measured.** It passes the self-test but has not been re-run
  against the tasks that exposed the bug.
- **Write cost:** each `/mimi-close` costs about $0.48. mimi is the cheapest per answer, but closing every
  session is not free.
- **Who wrote the tests:** the author wrote the facts and sessions for every experiment. Stage 1 reduced
  the home advantage (facts come up in passing, and continuity is automatic capture's strength), but did
  not remove it.
- **Parallel work:** two sessions closing on separate branches conflict in `STATE.md`.
- **Local by default:** `mimi/` is git-ignored, so memory is not shared or backed up by git unless you
  delete `mimi/.gitignore`. The evaluations tracked the memory files in the repository; agents load
  imported files either way.
- **Manual close:** memory is only as current as the last `/mimi-close`. `/mimi-logging` shows how many
  sessions ended without one.

**Total spend:** about $3.7 for Adopt, $1.4 for the two Check attempts, about $7 for Experiment 1, about
$2.5 for Experiment 2, about $8.8 for the write sessions, about $2 for recall, about $18 for the Opus reruns (Experiment 6: $6.0 retrieval, $9.3 write sessions, $2.8 recall) and about $1.5 for the `/session-close` smoke
test runs whose cost was recorded, and an estimated $8–10 for the handoff test (work and close costs
not captured; resumes $1.65). Judging is extra. That comes to roughly $55–65, plus about 420 judge calls for the dual re-grading.

---

## Files

| Path | Contents |
|---|---|
| `eval/harness/run.py` | Runner, dual judge and report (arms, task file and results folder set by env vars) |
| `eval/harness/stage1.sh`, `pilot.sh`, `proxy.py`, `tokens.py`, `analyze.py` | Experiment 8 driver, token-logging proxy, token accounting and bootstrap analysis |
| `eval/public/` | Experiment 7: `PROTOCOL.md`, and per repository the task files, `RESULTS.md`, verdicts and memory snapshots |
| `eval/stage1/` | Experiment 8: pre-registrations, task files and results |
| `eval/stress/s1/` | The script stress suite (`uv run --no-project --with pytest pytest eval/stress/s1`) |
