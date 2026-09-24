# django/django: memory-layer evaluation

## Repo
- https://github.com/django/django at `951d13c77bc120be385c46fc701a1ad93694edd1`: 34,949 commits, 7,091 files, Python.
- Base commit `9061125ac6` removes `.github/copilot-instructions.md`. That was the only agent-instruction file.
- The tasks were written from raw git (commit messages and diffs, read with `gh api` and `git show`) before any arm had memory. The sources are commits from 2024–2026: 356e5b0f5d, 00dca6f097, d992705f9e, 4bbc27c868, 424e0d8697, 5424151f96, 3dac3271d2, 1eac2659a1 and 25cf1cbb1c, plus `hashers.py` for T10.

## Arm builds (Opus)
| Arm | Cost | Turns | Memory lines | Auto-loaded bytes | check |
|---|---|---|---|---|---|
| B (harness) | $0.80 | 35 | 276: `CLAUDE.md` 48 + 7 files in `memory/` | 2,733 | n/a |
| D (memory layer, Adopt) | $0.24 | 10 | 85: `CLAUDE.md` 25, `STATE.md` 28, `ISSUES.md` 15, `decisions.md` 8 (empty), `memory/external.md` 9 | 2,584 | `memory layer clean` |

- **D content:** one issue (the fields.W225 GeneratedField false-warning revert) and one trap (the `[X.Y]` commit prefix for stable branches). Everything else was dropped as learnable from code or docs.
- **B content:** subsystem maps for the ORM, migrations, database backends, request handling, tasks and the test suite.

## Retrieval (Sonnet task model, 10 tasks × 2 reps)
| Arm | Sonnet judge | Opus judge | Mean | Disagreement | Wrong claims | Tools | Search | Input tokens | Cost/answer | Seconds |
|---|---|---|---|---|---|---|---|---|---|---|
| A (none) | 0.82 | 0.82 | 0.82 | 0.07 | 0.30 | 6.05 | 2.40 | 152k | $0.08 | 24 |
| B | 0.82 | 0.82 | 0.82 | 0.03 | 0.15 | 5.45 | 1.80 | 148k | $0.08 | 21 |
| D | 0.73 | 0.72 | 0.72 | 0.05 | 0.45 | 8.15 | 2.00 | 217k | $0.11 | 34 |

Per task (Sonnet judge, A / B / D):

| Task | Kind | A | B | D |
|---|---|---|---|---|
| T01 PBKDF2 non-UTF-8 bytes | bug | 1.00 | 1.00 | 1.00 |
| T02 DISTINCT ON / ORDER BY mismatch | bug | 1.00 | 1.00 | 1.00 |
| T03 `from_db()` fetch_mode TypeError | bug | 0.50 | 1.00 | 0.83 |
| T04 SQLite boolean index | bug | 0.67 | 0.67 | 0.33 |
| T05 `parse_header_parameters` via stdlib | decision | 1.00 | 1.00 | 1.00 |
| T06 Oracle 23c multi-row INSERT | decision | 1.00 | 1.00 | 0.67 |
| T07 PostgreSQL duplicate `_like` index | decision | 0.33 | 0.00 | 0.00 |
| T08 Safari fieldset flex | quirk | 1.00 | 1.00 | 1.00 |
| T09 SMTP non-ASCII local part | quirk | 0.67 | 0.50 | 0.50 |
| T10 default hasher | code | 1.00 | 1.00 | 1.00 |

Six of 60 answers had a judge split. Five of the six were on T09, where the key's wording (the rfc2047 bug vs. the CPython issue number) is ambiguous.

## Write and recall (E = B copy, F = D copy; 5 sessions, then 5 questions × 3 reps)
| Arm | Memory lines written | Facts persisted (of 5) | Recall, Sonnet | Recall, Opus | Wrong claims | Tools | Search | Cost/answer | Session cost |
|---|---|---|---|---|---|---|---|---|---|
| E | +39 / −2 (4 files) | 2: S2 decision to `memory/project-conventions.md`; S4 as a code note in `db-backends.md`, without the staging fact | 0.33 | 0.33 | 0.40 | 5.0 | 3.07 | $0.05 | $0.57 |
| F | +3 / −3 (`STATE.md` only, committed 3 times) | Only the last session's timeout line survives: "60 min, not 45" in `STATE.md` "Last session" | 0.47 | 0.40 | 0.20 | 3.9 | 0.73 | $0.05 | $0.72 |

Per question (Sonnet judge, E / F):

| Question | E | F |
|---|---|---|
| R1 Oracle 19c on self-hosted runner | 0.00 | 0.00 |
| R2 corrected timeout of 60 min | 0.67 | 1.00 |
| R3 BigAutoField + reason | 0.50 | 0.50 |
| R4 measurement | 0.00 | 0.00 |
| R5 staging MySQL non-strict | 0.50 | 0.83 |

- **S5 correction:** E never wrote the 45-minute figure, so there was nothing to correct. F's `STATE.md` records "60 min, not 45" only because it was the last session and `STATE.md` gets overwritten. The correction happened by overwrite, not by editing a fact in place.
- **`hygiene.py` fact tracking doesn't apply here.** Its fact patterns are hard-coded for the production project, so every fact row reads 0 for django. The facts were checked by hand with grep instead (see above). Its line counts are still valid.

## Transcript check (tasks where the arms differ: T03, T04, T06, T07, T09)
- **D:** every D run except one opened `ISSUES.md` and `decisions.md` (and `memory/`). They held nothing relevant to any task, so the reads added about 2.5 extra Bash/Read calls and roughly 43% more input tokens than A. They did not help.
- **D's lower score is not caused by memory content.** The D answers that missed (T04 rep 1, T06 rep 1) went wrong after digging through git. The memory was empty on these topics.
- **B:** no B run opened a `memory/` file for any task. B's T03 advantage (1.00 vs A 0.50) came from git search, not memory. At n=2 per task, B and A are the same.
- **Recall:**
  - F answered R2 from the auto-loaded `STATE.md` without searching (0.73 searches per answer vs 3.07 for E).
  - E had R3's reason in `memory/project-conventions.md`, but E_R3_0 and E_R3_1 never opened it. They answered from code, so the reason was lost at retrieval.

## Spend, breakage, cleanup
- **Model spend:** $9.38 from `result` events: builds $1.04, smoke $0.22, retrieval $5.34, sessions $1.29, recall $1.50. The judge calls (186 `claude -p` calls, costs not recorded by `run.py`) are estimated at about $5, for a total of about **$14–15**, under the $40 budget. The usage limit was never hit.
- **Codespace creation:** the account's two-running-codespace limit blocked creation for about 45 minutes, until another agent's codespace freed.
- **Token handling:** the local permission classifier refused the protocol's step that writes the OAuth token into `~/w/env.sh`. On the codespace a login shell (`bash -lc`) already has `CLAUDE_CODE_OAUTH_TOKEN` in its environment, so every model command ran through `bash -lc` and `env.sh` was never created.
- **Judge concurrency:** `run.py judge2` uses `ThreadPoolExecutor(6)`, which is 6 concurrent `claude` processes. It was patched to 3 on the Codespace to respect the concurrency limit.
- **Codespace deleted:** yes (`ml-django-r47jprw9gpq93vv4`, `gh codespace delete --force`, confirmed gone from `gh codespace list`).

## Most interesting observation
On a large, well-documented public repo, Adopt mode's one-minute test left almost nothing (85 lines, one issue, one trap). The layer then cost more on retrieval than having no memory: D always opened the empty `ISSUES.md` and `decisions.md` first, spent 43% more tokens and scored 0.72 vs 0.82.

In the write sessions, F applied the same test to the whole message. It judged "19c is supported" code-checkable and dropped the human-only half ("our CI runs 19c on a self-hosted runner with a 45-minute timeout"). Its only record of each fact was the `STATE.md` "Last session" line, which the next session overwrote, so four of five human facts were lost.
