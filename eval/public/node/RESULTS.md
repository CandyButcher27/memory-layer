# nodejs/node: evaluation results

## Repo
- URL: https://github.com/nodejs/node. Language: JavaScript/C++.
- Pinned SHA: `a2c8da59f2e319860985ff1275d66a6d16d611b0`. It has 48,620 commits and 51,849 tracked files.
- Clone: `--filter=blob:none`.
- Base commits:
  - `eval: strip agent instructions` removed the root `AGENTS.md`.
  - A second commit removed the vendored `deps/v8/GEMINI.md`, so every arm started equal.
- Arms were plain `cp -a` copies on `/tmp`, which had 106 GB free. `~/w/{src,base,arms,wr,snap}` were symlinks to it, because home had only 19 GB free and each copy is 1.2 GB.
- Tasks were written from commit messages and diffs I read myself, before any arm memory existed. I read them through `gh api` (raw commits) while waiting for a Codespace slot, then checked on the Codespace that every source commit is an ancestor of the pinned SHA. I also checked T10 and the reverted states for T05 and T06 against the code at that SHA.

## Arm builds
| Arm | Cost | Turns | Memory lines | Auto-loaded bytes | check |
|---|---|---|---|---|---|
| B (harness skill) | $1.13 | 43 | 371 (CLAUDE.md 43 + 8 memory files 328) | 2,644 | n/a |
| D (memory layer, Adopt) | $0.36 | 12 | 163 (CLAUDE.md 26, STATE 27, ISSUES 71 with 9 issues, decisions 8 as an empty template, embedding 26, external 5) | 2,921 | `memory layer clean` |

- Neither arm recorded any fact behind T05–T10.
- D's `ISSUES.md` ISS-1 and `memory/embedding.md` independently mined the T04 commit (the C++23 deadlock) from `git log`. B's memory describes subsystems (build, bootstrap, bindings, loaders, testing, deps) and has no incidents.

## Retrieval (10 tasks × 2 reps, Sonnet task model)
| Arm | Sonnet judge | Opus judge | Mean | Disagreement | Wrong claims per answer | Tools | Searches | Input tokens | Cost per answer |
|---|---|---|---|---|---|---|---|---|---|
| A none | 0.80 | 0.80 | 0.80 | 0.03 | 0.15 | 7.2 | 2.65 | 214k | $0.13 |
| B harness | 0.85 | 0.87 | 0.86 | 0.02 | 0.05 | 9.4 | 3.10 | 274k | $0.16 |
| D layer | 0.91 | 0.89 | 0.90 | 0.02 | 0.05 | 7.65 | 2.50 | 258k | $0.14 |

The wrong-claim, tool, token and cost columns come from `report_main.txt`, which uses the Sonnet verdicts.

Per task (A / B / D, Sonnet | Opus):

| Task | Kind | Sonnet | Opus |
|---|---|---|---|
| T01 odd-length hex Writev CHECK | bug | 1 / 1 / 1 | 1 / 1 / 1 |
| T02 toWeb hang on synchronous drain | bug | 1 / 1 / 1 | 1 / 1 / 1 |
| T03 zip FIFO hang (O_NONBLOCK) | bug | 1 / 1 / 1 | 1 / 1 / 1 |
| T04 C++23 range-for deadlock | bug | 1 / .83 / 1 | 1 / 1 / 1 |
| T05 FileHandle close-listener fix was reverted | decision | .50 / .50 / .75 | .50 / .50 / .75 |
| T06 ubuntu-slim for update workflows was reverted | decision | .50 / .67 / .50 | .67 / .67 / .50 |
| T07 AbortSignal leak warning off by default | decision | .50 / 1 / .83 | .33 / 1 / .67 |
| T08 AIX libc++ EEXIST for EACCES | platform | .50 / .50 / 1 | .50 / .50 / 1 |
| T09 AIX uv_random blocks on /dev/random | platform | 1 / 1 / 1 | 1 / 1 / 1 |
| T10 Buffer.poolSize and pool threshold | code | 1 / 1 / 1 | 1 / 1 / 1 |

The judges disagreed on 4 of 60 answers.

## Write and recall (5 sessions, then 5 questions × 3 reps)
| | E (from B) | F (from D) |
|---|---|---|
| Memory lines written | +34 −2 (memory/testing.md, README) | +35 −3 (external.md +26, decisions +6, STATE, CLAUDE.md index) |
| Committed | no; memory left untracked | yes, 5 `memory:` commits |
| S1 AIX 7.2 TL5 | not written | external.md |
| S2 no v22 backport decision | not written | decisions.md DEC-1 |
| S3 38.4 ms startup measurement | not written | not written: it judged the benchmark "readable from code" and noted only a pointer in STATE |
| S4 noexec /tmp trap | testing.md | external.md, with its own heading and index entry |
| S5 RAM correction 4 → 16 GB | written once as 16 GB, "not 4 GB as earlier assumed" (S1 had never stored the 4 GB) | edited in place in external.md and marked as corrected |
| Recall accuracy, Sonnet / Opus | 0.37 / 0.37 | 0.80 / 0.80 |
| Wrong claims per answer | 0.60 | 0.33 |
| Tools / searches per answer | 6.3 / 3.1 | 1.7 / 0.3 |
| Cost per answer | $0.08 | $0.03 |
| `check` after sessions | n/a | 1 finding: duplicate `Last verified:` in external.md |

Per recall question (E / F): R1 0 / 1, R2 0.17 (Opus 0) / 1, R3 0 / 0, R4 0.83 (Opus 1) / 1, R5 0.83 / 1.

When E's memory lacked a fact, it filled the gap from the repo. On R1 it answered "AIX 7.2 TL04" from BUILDING.md in all 3 reps, which is a confident wrong value. On R2 it answered "yes, technically" from the backporting policy.

## Transcript check (tasks where the arms differ)
- **T05, T07, T08:** no memory file held these answers in either arm, so the gaps are variance in search, not memory.
  - D opened ISSUES/decisions/memory at the start of T05 and T08 (a `Bash` cat or grep), found nothing relevant, and then searched git.
  - B touched `memory/` in T08 only.
- **T04:** D read `memory/embedding.md` and `ISSUES.md` in both reps and scored 1.0. B read memory once and scored 0.83 with the Sonnet judge; all three arms got it from git anyway.
- **Recall:** F went straight to the right file (a single Read of `memory/external.md` or `decisions.md`), which is why it used 1.7 tools per answer. E grepped `memory/` and then fell back to repo docs.

## Problems, spend, cleanup
- Waited about 2 hours for a Codespace slot, because the account limit is 2 running Codespaces. One process restart happened during the wait.
- Fixed a clone into a dangling symlink and fixed `cp -a` copying the symlink instead of its target. Patched `run.py` judge2 from 6 threads to 3. Replaced `hygiene.py`'s fact patterns with node-specific ones, and cross-checked by hand with grep.
- The session-limit error never appeared.
- Spend from `total_cost_usd`:

| Item | Cost |
|---|---|
| Builds | $1.49 |
| Retrieval runs | $8.75 |
| Write sessions | $1.44 |
| Recall | $1.60 |
| **Recorded total** | **$13.27** |

  - Judge calls (about 186 Sonnet and Opus calls) are not logged by `run.py`; I estimate them at about $5.
  - The total is about $18, against the $40 budget.
- **Codespace `ml-node-5gvwx456q4jxc7g99` was deleted.**
