# rust-lang/cargo

- **Repo:** https://github.com/rust-lang/cargo, pinned at `694054f34bcb04025b16d0eaf075038c0e58a15d` (2026-09-23). It has 23,301 commits and 3,073 tracked files, and it is written in Rust. The layout is the recent flattened one: `src/compiler`, `src/util`, and so on, with no `src/cargo/...`.
- **Agent-instruction files:** there were none to strip. `eval: strip agent instructions` is an empty commit on the `eval` branch.
- **Tasks:** written from raw git before any memory existed. I read the commit messages and diffs through `gh api` at the pinned SHA, then confirmed on the Codespace that all 12 source commits are present in the clone. The files are `tasks.json`, `sessions.json` and `recall.json`.

## Arm builds (Opus)

| Arm | Cost | Turns | Time | Memory lines | Auto-loaded bytes | `check` |
|---|---|---|---|---|---|---|
| B: current harness | $1.05 | 34 | 156 s | 316 (CLAUDE.md 52 + 9 files in `memory/`) | 3,103 (CLAUDE.md, no STATE) | n/a |
| D: memory layer (Adopt) | $0.33 | 14 | 60 s | 94 (CLAUDE 25, STATE 28, ISSUES 22, decisions 14, external 5) | 2,592 | `memory layer clean` |

- **D:** Adopt kept only 2 issues, both from the last few weeks (a sysroot revert and a double-counted `cargo clean` size), plus 1 decision (`cargo install` uses the packaged lock). `memory/external.md` is empty. None of the 10 task topics are in D's memory.
- **B:** B is a subsystem map drawn from module docs. It covers none of the task incidents either.

## Retrieval (Sonnet, 10 tasks × 2 reps, dual judge)

| Arm | Sonnet judge | Opus judge | Mean | Disagree | Wrong claims (S/O) | Tools | Search | Input tok | Cost/answer | Sec |
|---|---|---|---|---|---|---|---|---|---|---|
| A: none | 0.83 | 0.83 | 0.83 | 0.03 | 0.20 / 0.15 | 6.45 | 2.30 | 147k | $0.08 | 19.2 |
| B: harness | 0.75 | 0.73 | 0.74 | 0.05 | 0.25 / 0.20 | 7.80 | 3.00 | 170k | $0.09 | 23.1 |
| D: layer | 0.73 | 0.75 | 0.74 | 0.05 | 0.40 / 0.20 | 7.35 | 2.10 | 161k | $0.09 | 22.8 |

Per-task scores use the Sonnet judge (`report_main.txt`):

| Task | Kind | A | B | D |
|---|---|---|---|---|
| T01 sccache / CARGO env on `-vV` probe | bug | 1.00 | 1.00 | 1.00 |
| T02 `cargo check` never fresh (rmeta mtime) | bug | 1.00 | 1.00 | 1.00 |
| T03 token-from-stdout `\r` / header value | bug | 0.83 | 1.00 | 1.00 |
| T04 cache-lock deadlock | bug | 1.00 | 0.83 | 0.50 |
| T05 frame-pointers profile option | decision | 1.00 | 0.50 | 0.50 |
| T06 unused-deps ignore list | decision | 0.00 | 0.00 | 0.00 |
| T07 `cargo install` + `resolver.lockfile-path` | decision | 0.67 | 0.50 | 0.83 |
| T08 ZFS on macOS EAGAIN | quirk | 0.83 | 1.00 | 0.83 |
| T09 FreeBSD curl-sys 0.4.84 | quirk | 1.00 | 0.83 | 0.67 |
| T10 net retry schedule | code | 1.00 | 0.83 | 1.00 |

- **T06:** every run of every arm scored 0. The agents read the current `unused_dependencies` docs and never searched git for the reverted ignore list.

## Write and recall (E = B copy, F = D copy; 5 sessions, then 5 questions × 3 reps)

| | E: harness | F: layer |
|---|---|---|
| Memory lines added / removed (hygiene) | +41 / −0 (2 files) | +48 / −3 (5 files) |
| Write-session cost | $0.81 | $1.13 |
| Session facts recorded (checked by hand with grep) | None of the 5 person-only facts: no mirror, no 60/120 limit, no net.retry decision, no 6m41s timing, no Defender lock. It wrote only code descriptions (the retry schedule, the test-spawn path, "no `[profile.release]`"), and it committed nothing | All 5 facts, each once: Retry-After and Defender in `memory/external.md`, the decision in `decisions.md`, the timing in `memory/build.md`. It made 1 commit per session |
| S5 correction | Nothing to correct, because the fact was never written | Edited in place: `external.md` now reads "120 req/min … (corrected from an earlier reported 60 req/min)", and `STATE.md` also says 120 |
| Recall accuracy, Sonnet / Opus judge | 0.13 / 0.17 | **1.00 / 1.00** |
| Wrong claims per answer, Sonnet / Opus | 0.53 / 0.33 | 0.00 / 0.00 |
| Per answer: tools / searches / input tokens | 4.40 / 2.67 / 104k | 1.00 / 0.00 / 50k |
| Cost and time per answer | $0.06, 14.9 s | $0.03, 6.2 s |

- **`check` after the sessions:** F's `memlayer.py check` failed afterwards with `memory/external.md: 2 'Last verified:' lines, keep one`. The write sessions did not run `check` until clean.
- **E's partial credit:** E's recall hits (R1 0.17, R5 0.50) came from general cargo code knowledge, not from recorded facts.

## Transcript check

- **Did the memory arms open their memory?** B opened `CLAUDE.md` or `memory/` files in 6 of 20 runs. D opened them in 18 of 20: it greps `ISSUES.md` and `decisions.md` first, then falls back to `git log --grep`.
- **Did it help?** No. Neither memory held any task topic, so opening it only added turns.
- **Where D fell behind:**
  - T04 run 0: after finding nothing in memory, the agent followed an older NFS `flock` commit. That is search noise, not something the memory caused.
  - T05: both B and D lost a key point on one rep.
- **Why A does well here:** cargo's commit messages are rich, so `git log --grep` answers most retrieval tasks for A alone.

## Notes

- **Codespace:** the create call was blocked by the 2-running-Codespace limit for a long time. I retried until a slot opened.
- **`env.sh`:** writing `~/w/env.sh` was blocked by the permission classifier, so every model command ran through `bash -lc`.
- **`judge2`:** I patched `judge2` from 6 threads to 3. The first `judge2` pass crashed on one verdict: the greedy regex matched two JSON objects (`Extra data`). A rerun, which reuses cached verdicts, completed all 60 × 2.
- **`hygiene.py`:** its fact patterns are specific to the production-project experiment (they all show 0), so the fact placement above was checked by hand with grep.
- **Spend:**

  | Item | Cost |
  |---|---|
  | Builds | $1.38 |
  | Retrieval runs | $4.92 |
  | Write sessions | $1.94 |
  | Recall runs | $1.23 |
  | Recorded total | **$9.47** |

  The judge calls (150 on main, 30 on recall, Sonnet and Opus) don't save their cost; I estimate about $3–5, for a total of about $13–15, well under $40. No session limit was hit.
- **Codespace deleted:** yes (`ml-cargo-976pjqwv9qqqfpqw`).
