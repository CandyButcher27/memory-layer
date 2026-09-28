# State
<!-- Now only. Overwritten every session. Finished work leaves. Cap 60 lines. -->

Goal: Python CLI utility and library for manipulating SQLite databases (README.md).

## Deployed
Latest release 4.2.1 (28dc627). main is 5 commits ahead (up to 6bc1d33), unreleased.

## Broken
- `insert --csv` type detection coerces zip-code-like columns to integer, dropping the leading zero. Diagnosed, not yet fixed — see ISSUES.md ISS-7.

## Open threads
- Need date/commit/ticket for the production incident where `--replace` wiped enrichment columns, before it can go into decisions.md as a DEC entry (policy: always `--upsert` with explicit `--pk`, never `--replace`).
- `sqlite-utils rows --sample N` feature: step 1 done (see below), steps 2-3 remain.

## Next 3
1. Write a failing test for ISS-7 (zip-code/leading-zero bug) - `tests/test_utils.py` against `ValueTracker`/`TypeTracker` directly, plus a CLI-level `insert --csv` test - then fix `test_integer` and update ISS-7 to Status: fixed with the commit.
2. Step 2: wire `--sample` into the `rows` CLI command (`sqlite_utils/cli.py`, `rows()` near line 2452). Must be mutually exclusive with `-o/--order` (line 2431) - raise a `click.UsageError` if both given, matching the `ValueError` `rows_where()` already raises when `sample` is combined with `order_by`.
3. Step 3: add tests (`rows_where(sample=...)` and the CLI `--sample`/`--order` conflict) and a docs entry (cli-reference / python-api); then get the checkable detail for the `--replace` incident (still blocked on user).

## Last session (2026-09-28)
<!-- Rewritten at every close, ~10 lines. Where the last session stopped, so the next one resumes cleanly. -->
Branch: detached HEAD at 6bc1d33
Uncommitted: CLAUDE.md, ISSUES.md, STATE.md, decisions.md, memory/ (new), sqlite_utils/db.py (modified)
Stopped at: diagnosed ISS-7 (zip-code truncation bug) down to `ValueTracker.test_integer`; no code changed yet, just investigation - recorded in ISSUES.md. Earlier in the session: added `sample: int | None = None` (keyword-only) to `Queryable.rows_where()` in sqlite_utils/db.py - does `order by random() limit N`, raises `ValueError` if combined with `order_by`/`limit`/`offset`. Not committed. CLI wiring, tests, and docs deliberately deferred (see Next 3). Recorded DEC-3 in decisions.md: `order by random() limit N` beats a random-offset approach (user had tried offset-based sampling last week and hit duplicate rows + WITHOUT ROWID breakage).
Tried, failed: random-offset sampling (`offset abs(random()) % count`) - not implemented in this repo, rejected before coding per user's prior experience; see DEC-3.
Resume with: write the failing test for ISS-7 first (Next 3 item 1), then fix `test_integer`; after that, step 2 CLI wiring for `--sample`; still need the checkable detail (date/commit/ticket) for the `--replace` incident to close that open DEC thread.

Last updated: 2026-09-28
