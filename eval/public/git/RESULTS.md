# git/git: public-repo evaluation

Run 2026-09-23/24 on a Codespace (standardLinux32gb, Claude Code 2.1.281), following `eval/public/PROTOCOL.md`.

## Repo
- **URL:** https://github.com/git/git
- **Pinned SHA:** 3bc0341126508f78f5869cbfc0005e987efdf0c7 (Git 2.56-rc2)
- **Size:** 82,306 commits, 4,852 tracked files. Language: C, with shell tests.
- **Agent-instruction files:** none were present, so the base commit `eval: strip agent instructions` is empty.

## Tasks (written from raw git before any arm existed)
| ID | Kind | Source | Topic |
|---|---|---|---|
| T01 | recurring bug | e4621a0169 | `rev-parse` slows from 0.4s to 4.5s with about 38k packs (O(N²) packfile list) |
| T02 | recurring bug | 1034ad383f | `clone --revision` segfaults over protocol v0 (`peer_ref` NULL) |
| T03 | recurring bug | 57246b7c62 | `merge-file --object-id` hits a BUG in a linked worktree |
| T04 | recurring bug | 81cf6ccc29 | `log -L` plus `-G`/`-S` hits an assertion (pickaxe breaks rename detection) |
| T05 | decision | 8b44deebaf | `clean_on_exit` to reap transport children was reverted (shell/mksh deadlock) |
| T06 | decision | a12382f994 | midx v2 as the default was reverted (older Git `die()`s on it) |
| T07 | decision | 8fb6d11fad | `--stdin-packs` in midx repack was reverted |
| T08 | platform | d48c5d5a4c | Dash 0.5.13 drops a byte on read, so t9300 hangs |
| T09 | platform/CI | fddb484255 | Ubuntu 25.10 sudo-rs has no `--preserve-env` |
| T10 | code | run-command.c, test-lib.sh | `maintenance.autoDetach`, `gc.autoDetach` and `GIT_TEST_MAINT_AUTO_DETACH` |

The session facts were invented for the test: S1 is Alpine 3.20/musl runners with a 45-minute cap. S2 keeps reftable off the default because backups rsync `refs/`. S3 is a `git status` measurement: 1.8 s / 0.4 s, 15 runs, 2.1M files, 2026-09-20. S4 is a proxy that strips `Git-Protocol`, so fetches fall back to v0. S5 corrects the cap to 60 minutes.

## Arm builds
| Arm | Turns | Cost | Memory lines | Auto-loaded bytes | `check` |
|---|---|---|---|---|---|
| A: none | – | – | 0 | 0 | – |
| B: harness | 27 | $0.69 | 220 (CLAUDE.md plus 4 component files: build/Rust, ODB, refs, testing) | 2,427 | – |
| D: memory layer (Adopt) | 11 | $0.35 | 114 (3 ISSUES from recent `git log`, 1 decision on Rust, 2 external traps) | 2,686 | memory layer clean |

Neither memory covers any of the 10 task topics. That is expected: the repo had no prior agent memory, so both layers were built cold.

## Retrieval: Sonnet task model, 10 tasks × 2 reps × 3 arms
| Arm | Sonnet judge | Opus judge | Disagree | Wrong claims | Tools | Search | Input tokens | Cost/run | Secs |
|---|---|---|---|---|---|---|---|---|---|
| A | 0.77 | 0.77 | 0.00 | 0.45 | 9.4 | 2.7 | 266k | $0.13 | 50 |
| B | **0.80** | **0.80** | 0.00 | 0.40 | 12.9 | 4.15 | 432k | $0.20 | 67 |
| D | 0.62 | 0.63 | 0.05 | 0.40 | 11.7 | 1.6 | 340k | $0.16 | 50 |

Per task, Sonnet judge (A / B / D). Opus differs only on D_T05_1 and D_T06_0.

| Task | A | B | D |
|---|---|---|---|
| T01 | 1.00 | 1.00 | 1.00 |
| T02 | 1.00 | 1.00 | 1.00 |
| T03 | 0.67 | 0.67 | 0.50 (one run hit max-turns and gave no answer) |
| T04 | 1.00 | 1.00 | 1.00 |
| T05 | 0.00 | 0.00 | 0.33 |
| T06 | 0.67 | 1.00 | 0.33 |
| T07 | 0.83 | 0.50 | 0.33 |
| T08 | 1.00 | 0.83 | 0.67 |
| T09 | 1.00 | 1.00 | **0.00** |
| T10 | 0.50 | 1.00 | 1.00 |

## Write and recall (E = B copy, F = D copy; 5 sessions, then 5 questions × 3 reps)
| | E: harness | F: memory layer |
|---|---|---|
| Write-session cost | $0.84 | $1.22 |
| Memory lines added/removed | +105 / −2 in 4 files (2 new topic files) | +44 / −5 in 4 files (committed in 3 commits) |
| S1 runners fact | `memory/testing.md` | `memory/external.md` + `CLAUDE.md` index line |
| S2 decision | new `memory/project_ref-format-default-policy.md` | `decisions.md` DEC-2 |
| S3 measurement | **not written** | **not written** ("derivable from the code in under a minute") |
| S4 proxy trap | new `memory/transport-http-protocol-v2.md` + README | `memory/external.md` + index |
| S5 correction | Edited in place: "60 minutes… corrected from an earlier 45" | Edited in place in `external.md`, index line and `STATE.md` |

| Arm | Sonnet | Opus | Disagree | Wrong | Tools | Search | Input tokens | Cost/answer | Secs |
|---|---|---|---|---|---|---|---|---|---|
| E | 0.30 | 0.33 | 0.03 | 0.87 | 8.3 | 3.2 | 201k | $0.09 | 33 |
| F | **0.73** | **0.70** | 0.03 | **0.33** | **1.5** | **0.0** | **64k** | **$0.03** | **8** |

| Question | E | F |
|---|---|---|
| R1 runner OS/libc | 0.00 | 1.00 |
| R2 reftable decision | 1.00 | 1.00 |
| R3 status measurement | 0.00 | 0.00 (never written in either arm) |
| R4 proxy trap | 0.17 | 0.67 |
| R5 corrected cap (60) | 0.33 | 1.00 |

E wrote the facts, but its recall sessions opened memory in only 9 of 15 runs. On R1 and R5 they searched `.github/workflows` and answered "no self-hosted runners exist". F opened memory in 15 of 15 runs and never needed a search.

## Transcript check (where the retrieval arms differ)
| Arm | Runs that opened memory | Runs that used `git log`/`show`/`blame` |
|---|---|---|
| A | 0/20 | 17/20 |
| B | 6/20 | 15/20 |
| D | 17/20 | 13/20 |

- **T09 (D 0.00 vs A/B 1.00):** both D runs started with `cat ISSUES.md decisions.md STATE.md`, found no entry, and answered "no known issue recorded here". Neither ran `git log`. Arm A found fddb484255 with `git log --grep=sudo` on its second call.
- **T06 (D 0.33 vs B 1.00):** D read `decisions.md`, found nothing, and then answered from current code ("still defaults to v1") without the revert history or its reason.
- **T10 (A 0.50 vs B/D 1.00):** neither memory holds this. The difference is run-to-run variance: A went to `builtin/gc.c` instead of `run-command.c`.
- **Did memory help?** On retrieval, no memory file contained any task's answer in either arm, so memory could not help. The memory-first rule in D's `CLAUDE.md` hurt: a miss in a thin memory was read as "not a known issue". In the recall test, the layer's index made the difference, with 3× cheaper answers and 2.4× the accuracy.

## What broke or deviated
- `run.py judge2` uses `ThreadPoolExecutor(6)`, which runs up to 6 `claude` processes at once. I changed my Codespace copy to 3 to respect the 3-process limit. The copied `run.py` shows the change.
- `hygiene.py`'s fact regexes are specific to the production-project experiment, so every row reads 0. The fact routing above was checked by hand with grep.
- D_T03_0 hit `--max-turns 40` and gave no answer. It is kept and scored 0.
- Judge spend is not logged by `run.py`. I estimated it from one measured call per judge model: Sonnet $0.026, Opus $0.057.

## Spend
| Item | USD |
|---|---|
| Arm builds B + D | 1.04 |
| Retrieval runs (60) | 9.81 |
| Write sessions (10) | 2.06 |
| Recall runs (30) | 1.91 |
| Judges (about 90 answers × 2 models, estimated) | ~7.5 |
| Auth check, cost probes | ~0.1 |
| **Total** | **~$22.4** of the $40 budget |

No session-limit errors occurred.

**Codespace `ml-git-v6pxqgw4vrg53wpjw` was deleted: yes.** `gh codespace list` shows no `ml-git`.

## Most interesting observation
The memory-first habit backfired on retrieval. D's layer was built cold from git history and held only 6 facts. Its `CLAUDE.md` sends the agent to `ISSUES.md` first, so on T09 (sudo-rs) both D runs read an empty-for-this-topic ISSUES file, concluded "no known issue", and never ran the `git log --grep` that got arm A a perfect score. On a repo with excellent commit messages, a thin memory that is treated as authoritative is worse than none. The same index made the layer much better on facts that only exist in memory (recall 0.73 vs 0.30, at a third of the cost). The layer needs a rule like "a miss in memory is not evidence of absence; fall back to `git log --grep`".
