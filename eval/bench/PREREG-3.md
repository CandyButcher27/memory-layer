# Bench: pre-registration

Written 2026-10-03, before any bench run. Nothing in this file changes after the first result arrives.
Stage 1 ([`../stage1/PREREG.md`](../stage1/PREREG.md)) and its follow-up
([`../stage1/PREREG-2.md`](../stage1/PREREG-2.md)) are not changed. The bench runs the follow-up and adds two new
questions.

## Questions

1. **Rivals.** How does mimi compare with the most-used Claude Code memory tools, on Stage 1's sqlite-utils
   tasks?
2. **Follow-up.** Does the `/mimi-close` scope fix work? Does mimi beat auto-memory on continuity? These are
   PREREG-2's Run 1 and Run 2.
3. **Long horizon.** Does mimi keep its lead in the following cases?
   - over 12 sessions, where facts are corrected and threads span several sessions
   - for facts the agent finds in files, which the user never says (the case automatic capture is built for)
   - when the user forgets to run `/mimi-close`

## Arms

| Arm | Memory | Install |
|---|---|---|
| A | None | Auto-memory off |
| N | Claude Code built-in auto-memory | Nothing installed |
| D | mimi, with a `/mimi-close` turn at the end of every session | Adopt build. Auto-memory off |
| D0 | mimi, never closed: a copy of D's Adopt build, no close turn | Auto-memory off |
| M | claude-mem (thedotmack/claude-mem, ~95k stars): npx CLI 13.28.0; the worker is the marketplace plugin, 13.29.0 at setup | `npx claude-mem install --provider claude`, then re-registered with the CLI. Auto-memory off |
| G | agentmemory 0.9.29 (rohitg00/agentmemory, ~29k stars) | Server through npx in keyless default mode, plus its Claude Code plugin (hooks + MCP). Auto-memory off |
| R | claude-remember (Digital-Process-Tools) | Plugin `remember@dpt-plugins`. Auto-memory off |
| L | claude-mem-lite (sdsrss) | Plugin `claude-mem-lite@sdsrss`. Auto-memory off |
| K | recall (raiyanyahya/recall, ~750 stars) | Plugin `recall@recall`, fully local, no model calls. Auto-memory off |
| S (not run yet) | Supermemory (supermemoryai, ~31k stars; Claude Code plugin supermemoryai/claude-supermemory) | Plugin `supermemory@supermemory-plugins` on the hosted API with the user's key, one container per track. Auto-memory off |

- Every rival runs with its default settings.
- Plugin versions are whatever the marketplace serves at setup. They are recorded in `install_<arm>.txt`.
- Each arm runs with its own `HOME`.
- Arms run one at a time, and each tool's background process is stopped between jobs.

## Tracks

| Track | Repo | Arms | Tasks | Reps |
|---|---|---|---|---|
| `rivals` | sqlite-utils `6bc1d33` | D N M G R L K | Stage 1 sqlite-utils: 5 sessions, 8 fact questions + 2 continuity questions | 3 (facts), 5 (continuity) |
| `f2b-sqlite` | sqlite-utils `6bc1d33` | D N M A | PREREG-2 F2b: 4 threads | 5 |
| `long` | sqlite-utils `6bc1d33` | D D0 N M G R K A | [`tracks/long/`](tracks/long/): 12 sessions, 18 questions | 2 |
| `f2b-cargo` | cargo `694054f` | D N M A | PREREG-2 F2b on cargo | 5 |

Tracks run in that order, and the Opus judge runs after every track has its Sonnet verdicts.

### The long track

There are 18 questions, grouped by family:

| Family | Questions | What happens in the sessions |
|---|---|---|
| stated | Q01–Q08 | The user mentions a fact in passing, next to a real code question: a person, an external limit, a decision, a deadline, a review rule, a measurement, an infrastructure detail, a trap |
| corrected | Q09–Q11 | Facts superseded later: a start time changed once, a Python version changed twice, an owner replaced |
| discovered | Q12–Q15 | The user points the agent at a file outside the repo (`/tmp/incoming/…`) and asks about it. The file is deleted after the session. The answer exists only in what the agent read: a failure log, a Lambda config, a benchmark table, a Latin-1 CSV. The user never states the answer |
| repo | Q16 | Answerable from the code alone. This is a control for cost, not for memory |
| continuity | Q17–Q18 | A feature carried over sessions 3 and 7, and an investigation over sessions 4 and 10, with other sessions in between. The resume question asks for the latest state |

Sessions 11 and 12 add distance before the questions.

## Protocol

These details are the same as in Stage 1:

- Sonnet is the task model, with `--max-turns 40`. Answers end with the Stage 1 eval suffix.
- Each eval run restores the arm's saved post-write state, so no answer sees another answer's session.
- Judges: Sonnet, then Opus, with the Stage 1 judge prompt. Accuracy is the share of key points hit, averaged
  over the available judges. Wrong claims are counted per answer.

These details differ from Stage 1, and all are fixed in advance:

- **Auth and billing:**
  - Runs use a Claude Pro subscription token (`claude setup-token`), not an API key.
  - Cost is the `total_cost_usd` that Claude Code reports, which is an API-equivalent figure.
  - Runs pause at the 5-hour usage limit and resume on the next hourly tick.
- **Permissions:** `--permission-mode bypassPermissions` in every arm.
  - Write sessions disallow only `Agent Task WebFetch WebSearch`.
  - Eval runs also disallow `Edit Write NotebookEdit`.
  - This lets each rival's MCP tools run without naming them per arm.
- **mimi's Adopt build** uses Opus, as in Stage 1. If the subscription refuses Opus, the build switches to
  Sonnet, and that change is logged as a deviation.
- **Usage limit during a write session:** the arm is restored to its state before the session, and the
  session is re-run in full later. Two signals count as a limit hit:
  - Claude Code's own error result.
  - A usage-limit message in a background tool's files written during the session.

## Decision rules

Differences are paired by question and run. The 95% interval is a bootstrap over questions.

**Rivals.** For each rival X in M, G, R, L and K, over all 10 questions:
- If D − X ≥ 0.15 with an interval excluding 0, then *mimi beats X*.
- If |D − X| < 0.10, it is *a tie*.
- If X − D ≥ 0.15 with an interval excluding 0, then *X beats mimi*.
- Anything else is *no difference shown*.

The README states each result as it comes out, including ties and losses.

**Follow-up.** PREREG-2's rules apply as written:
- Run 1 is judged on the rivals track's D arm: R1 and R4 must each reach ≥ 0.67, and no other question may drop
  more than 0.25 below its Stage 1 D score.
- Run 2 is the `f2b-sqlite` track, then `f2b-cargo`.

**Long horizon:**
1. **Primary, D vs N over all 18 questions:**
   - D − N ≥ 0.10 with an interval excluding 0: *mimi beats auto-memory over the long horizon*.
   - |D − N| < 0.10: *a tie*.
   - N − D ≥ 0.10 with an interval excluding 0: *auto-memory wins*.
2. **Secondary:** D vs M, G, R and K, with the same thresholds.
3. **Forgetting to close:**
   - D − D0 and D0 − N are reported.
   - If D0 < N + 0.05, the README says that mimi's lead depends on running `/mimi-close`.
4. **Discovered facts** (Q12–Q15):
   - With only 4 questions, this family is descriptive.
   - If any capture tool (M, G, R or K) scores ≥ 0.15 above D on it, the README says so.
5. **Corrected facts** (Q09–Q11): wrong claims per answer are reported for each arm.
6. **Q16:** tokens and tool calls per answer are reported. Accuracy is expected to be near the ceiling for every
   arm.
7. **Cost:** tokens and cost per answer, and write-phase cost per arm, are reported, with no threshold.

## Validity checks

- **Write sessions:** every turn finishes without an error. A hit of the 40-turn cap is flagged, as in
  Stage 1.
- **Retries:** a job that fails 3 times is skipped and listed as failed. A rival with a skipped write session is
  reported as invalid for that track.
- **Planted files:** every planted file is deleted before the next job. The working tree is not allowed to
  contain them, because a commit would put them into git history. A planted file that does reach git history
  invalidates that arm's discovered family.
- **Rival installs** pass a smoke test before their first write session. The rival's own store must show at
  least one capture after the first session (observations, files or rows). An arm that captures nothing after
  every session is reported as such, not dropped, as M was in Stage 1.

## Known limits, stated in advance

- I (Claude, the same model family as mimi's author and the judges) wrote the long track's facts and sessions.
  Some home advantage remains. The discovered family and the D0 arm are there to test mimi where it should
  be weak.
- **Usage limits can stall background capture.** Rivals that summarise with Haiku in the background may hit the
  limit silently. The detection is a text match on their files, so it can miss a silent failure.
- **Supermemory's store is in the cloud, so a restore cannot reset it.**
  - Its eval runs set the plugin's `signalExtraction` to a keyword that never occurs, so eval sessions capture
    nothing.
  - Recall is unchanged.
  - A usage-limit restore of an S write session cannot undo what was already uploaded, so a re-run may leave
    duplicate memories. Retries are logged.
- Sessions are headless, there is one repo per new track, and the n is small: 18 questions × 2 runs for the long
  track.

## Deviations, recorded 2026-10-04 before any rival eval answer exists

To fit the run inside Pro usage limits, two changes were made after mimi's rivals-track run and before any rival arm
reached its eval phase:

1. **Sonnet is the only judge.**
   - On mimi's 34 rivals answers, Opus and Sonnet agreed on every key point.
   - The Opus verdicts already written for D are kept on disk but are not used in any report, so every arm is scored
     by the same judge.
2. **Every question runs 3 times**, including the continuity questions in `rivals`, `f2b-sqlite` and `f2b-cargo`
   (previously 5).
   - D's rivals track already has runs 3 and 4 of C1 and C2. Paired differences use only the runs both arms have.
   - The interval is a bootstrap over questions, so this widens it only slightly.

PREREG-2's Run 2 rules are applied with 3 runs per question instead of 5.

## Deviation, recorded 2026-10-04 before any agentmemory session completed

`rivals:write:S1:G` failed twice with `arms.sh up` timing out after 1800 s. The cause was the bench, not
agentmemory: the backgrounded server's subshell kept bench.py's output pipe open, so `subprocess.run` never
returned although `up` had exited 0 within seconds. The redirect now covers the whole subshell. The job's
failure count was reset to 0, because neither failure reached the tool under test.

Dumping the rival stores after S1 showed two installs that captured nothing:

- **claude-remember (R):** every background save failed with `Not logged in · Please run /login`. Claude Code does
  not pass `CLAUDE_CODE_OAUTH_TOKEN` to hook processes (checked with a probe hook, also when the token is set in
  settings.json `env`). The install now sets the plugin's own `oauth_token` option to the bench token, which is
  the vendor's documented fix.
- **claude-mem-lite (L):** no database was ever created. Version 6.21.0 and its better-sqlite3 13 need Node >= 22,
  and WSL had Node 20, where the compiled binding crashes on open. Arm L now runs with Node 22 on its PATH.

Both arms' rivals state was moved to `~/bench/invalid/` and both were reinstalled and re-run from setup. The
sessions they ran before the fix are not used.

claude-mem-lite has no token option, so its own `claude` calls from hooks stayed logged out after the Node fix.
The user logged in once with `/login` inside arm L's HOME on the bench account, as a real user would be. Snapshots
now skip `.claude/.credentials.json`, so a restore never rolls back a refreshed login. L was reset again and
re-run from setup with the login in place.

The capture check in Validity checks is now automatic, because two rivals passed every job while storing nothing:

- After each write session, files the arm wrote are searched for `Not logged in`.
- After a track's first session, each rival's store must hold a record from the arm's project:
  claude-mem an observer session that got a reply (its observer may skip every event of a read-only session), agentmemory a session started in the arm's repo with at least one observation, remember a non-empty `now.md` or a logged Haiku call (it may answer SKIP on a read-only session),
  claude-mem-lite a session summary, recall a non-empty `history.md`.
- Either failure writes `~/bench/halt`. No tick runs until a person deletes it, and the session restores from its
  pre-session snapshot.
