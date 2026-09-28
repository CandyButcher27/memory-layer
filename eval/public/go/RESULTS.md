# golang/go: memory-layer evaluation

## Repo
- https://github.com/golang/go, pinned at `41fd3e5b1beb89d949bb26b5cc6842174861f5b8` (2026-09-24)
- 67,724 commits and 15,954 tracked files. Language: Go.
- The repo had no agent-instruction files, so the strip step committed nothing.

## Arm builds (claude -p --model opus)
| Arm | Cost | Turns | Time | Memory lines | Auto-loaded bytes | check |
|---|---|---|---|---|---|---|
| B: current harness | $0.77 | 31 | 154 s | 286 (`CLAUDE.md` 47 + 8 `memory/` files, 239) | 2,756 (`CLAUDE.md`) | n/a |
| D: memory layer (Adopt) | $0.30 | 14 | 66 s | 101 (`CLAUDE.md` 25, `STATE.md` 28, `ISSUES.md` 15, `decisions.md` 8, `memory/external.md` 25) | 2,983 (`CLAUDE.md` + `STATE.md`) | `memory layer clean` |

D's Adopt found almost nothing it could check: one open issue (the LUCI builder-detection revert over a read-only GOROOT), no decisions, and Gerrit/CLA/commit-message conventions. B wrote subsystem overviews (bootstrap, compiler, cmd/go, runtime, testing, FIPS).

## Tasks
There are 10 retrieval tasks (4 recurring bugs, 3 decisions, 2 platform quirks, 1 code control). Every answer key comes from commit messages and diffs from 2024 to 2026: 974764364a, 385dc33250, 098a87fb19, c3c65602d6, 1b3db48db7, ae62a1bd36, 9a9246555f, 3aeef4896d, 04dc12c1a1, and `net/http/transport.go`. The keys were written before any arm existed. I read the commits through the GitHub API while waiting for a Codespace slot, then confirmed each one in the clone.

## Retrieval (Sonnet, 10 tasks × 2 reps)
| Arm | Sonnet judge | Opus judge | Mean | Disagree | Wrong claims | Tools | Search | Input tokens | Cost/answer | Time |
|---|---|---|---|---|---|---|---|---|---|---|
| A: none | 0.82 | 0.80 | 0.81 | 0.02 | 0.15 | 5.3 | 1.5 | 137k | $0.07 | 20.5 s |
| B: harness | 0.80 | 0.82 | 0.81 | 0.02 | 0.20 | 7.9 | 2.7 | 209k | $0.11 | 32.5 s |
| D: layer | 0.77 | 0.82 | 0.79 | 0.05 | 0.20 | 7.6 | 2.0 | 210k | $0.10 | 33.0 s |

Per-task scores (Sonnet judge, A / B / D):
- T01 0.67/0.67/0.67
- T02, T03, T08, T09, T10: 1.00 on every arm
- T04 1.00/0.50/1.00
- T05 0.50/0.83/0.33
- T06 0.00/0.00/0.17
- T07 1.00/1.00/0.50

The memory arms are no better than no memory, and they cost about 50% more tokens per answer. This is expected: neither adopted memory contained anything about these ten incidents.

## Write and recall (5 sessions, then 5 questions × 3 reps)
| | E (from B) | F (from D) |
|---|---|---|
| Memory lines written | +107 / −4 (net +103), 4 files | +66 / −4 (net +62), 6 files, 3 commits |
| Session cost | $0.91 | $1.11 |
| Recall accuracy, Sonnet / Opus judge | 0.23 / 0.33 | 1.00 / 1.00 |
| Wrong claims per answer | 0.67 | 0.00 |
| Tools / search per answer | 5.1 / 1.9 | 1.3 / 0.1 |
| Cost per answer | $0.06 | $0.03 |
| S5 correction (kernel 5.4 → 5.15) | Edited in place: 5.4 is gone and 5.15 is in `memory/os-exec-pidfd.md` | Edited in place: `memory/os-exec.md` says "5.15 (corrected 2026-09-24 from an earlier 5.4)". The `STATE.md` handoff mentions both |

Per question (E / F):
- R1 (pidfd/seccomp): 0.67 / 1.00
- R2 (disablethp decision): 0.17 / 1.00
- R3 (make.bash timing): 0.00 / 1.00
- R4 (tmpfs /tmp trap): 0.00 / 1.00
- R5 (corrected kernel): 0.33 / 1.00

I checked where each fact landed by hand with grep, because `hygiene.py`'s fact patterns are specific to the production-project experiment. Its line counts are still valid.

**E (harness) never wrote three of the five person-only facts:**
- S3 (2m41s median, 5 runs, 2026-09-20) is missing.
- S4 (the 512 MB tmpfs and `GOTMPDIR=/scratch/gotmp`) is missing.
- For S2 it wrote how the runtime implements `disablethp`, not the team decision "all services run with disablethp=1, runtime default not patched".
- It did store S1 and S5 in a 64-line code walkthrough of pidfd.
- Even so, 2 of 3 R5 runs and 1 of 3 R1 runs declined to answer or treated the memory note as unverified.

**F (layer) routed every fact to one place:**
- S2 to `decisions.md`
- S3 to `memory/build-perf.md`
- S4 to `memory/external.md`
- S1 and S5 to `memory/os-exec.md`

## Transcript check
- **Retrieval:** where B and D differ (T04, T05, T07), the difference tracks whether the run ran `git log` / `git show`, not memory use.
- **B runs never opened memory.** D opened it in 2 runs:
  - In D_T05_0 it looked at memory, found nothing, never searched git, and scored 0.
  - In D_T07_0 it looked at memory, then ran git, and scored 1.0.
- **Recall:** memory decided the outcome. F answered from its memory files in about 1 tool call. E dug through code and git with about 5 calls and often came back empty.

## Problems, spend, cleanup
- **Waiting and restarts:** I waited several hours for a Codespace slot (the account allows 2, and they were shared with other agents). There was also one local network drop and one process restart before the Codespace existed. Once it was up, nothing failed.
- **judge2 threads:** I patched `run.py` judge2 from 6 threads to 3 to respect the concurrency limit.
- **Measured model spend:** $10.20.
  - Builds: $1.07
  - Retrieval: $5.74
  - Sessions: $2.03
  - Recall: $1.37
- **Judges:** 180 judge calls (plus 6 in the smoke test) did not record their cost. My estimate is $6–10, which puts the total at about $16–20, under the $40 budget.
- **Codespace:** `ml-go-7v7gprwq97qx2x756` was deleted at the end. Yes.
