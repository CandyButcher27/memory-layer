# Issues
<!-- Append-only, one entry per bug:
"## ISS-<n> — <title>" heading, then
Symptom: exact error text or observed behavior
Cause: root cause
Fix: commit hash
Test: the test that fails without the fix
Status: open | fixed -->

## ISS-1 — sqlite-utils 4.2 crashes on start when installed without dev dependencies
Symptom: `sqlite-utils` 4.2 crashed on import in a normal install; `uv run --no-default-groups sqlite-utils --help` fails (GitHub #842).
Cause: `sqlite_utils/db.py` imported `Self` from `typing_extensions`, which is only present via the dev dependency group, not in `[project] dependencies`.
Fix: f6d7311 (released as 4.2.1, 28dc627)
Test: CI step "Check no accidental dev= dependencies needed" in `.github/workflows/test.yml`; locally `just test-no-dev-dependencies` (56dd097)
Status: fixed

## ISS-2 — ResourceWarning for unclosed buffered reader from rows_from_file()
Symptom: running tests with `-Wall` (seen via `just test -Wall` in the LLM project) reports unclosed-file ResourceWarnings from format detection in `rows_from_file()`.
Cause: the `io.BufferedReader` wrapper used to peek at the first bytes was never closed on the empty-input and JSON paths.
Fix: 6bc1d33
Test: tests/test_rows_from_file.py::test_detect_format_closes_eager_reader, ::test_detect_format_closes_reader_on_invalid_json
Status: fixed

## ISS-3 — Failed db.execute() write leaves a phantom transaction open
Symptom: after a write through `db.execute()` raises, every later write joins the driver's still-open implicit transaction and is silently rolled back when the connection closes.
Cause: the implicit transaction opened by the failed statement was never rolled back.
Fix: 7d86118 (refs GitHub #769 review comment)
Test: tests/test_atomic.py::test_execute_failed_write_rolls_back_implicit_transaction
Status: fixed

## ISS-4 — db.query("; COMMIT") bypasses the first-token scanner
Symptom: `db.query("; COMMIT")` (or a leading UTF-8 BOM) committed the caller's open transaction, then raised a confusing `OperationalError`; `db.execute("; BEGIN")` auto-committed the transaction it opened.
Cause: `_first_keyword()` did not skip leading `;` and BOM, which the sqlite3 driver tolerates before the first token.
Fix: adc10df (refs GitHub #769 review comment)
Test: tests/test_query.py::test_query_prefixed_commit_does_not_commit_transaction
Status: fixed

## ISS-5 — OperationalError "no such savepoint" masks the real IntegrityError
Symptom: a `RAISE(ROLLBACK)` trigger or `INSERT OR ROLLBACK` conflict inside `atomic()` / `query()` surfaced as `OperationalError: no such savepoint` or `cannot rollback - no transaction is active` instead of `sqlite3.IntegrityError`.
Cause: the error had already destroyed the whole transaction and its savepoints; the cleanup path tried to roll back anyway.
Fix: d9a0fd2 (cleanup checks `conn.in_transaction` first)
Test: tests/test_query.py::test_query_preserves_error_from_transaction_destroying_trigger
Status: fixed

## ISS-6 — CI "Install SpatiaLite" step fails with apt 404
Symptom: `apt-get install libsqlite3-mod-spatialite` on the ubuntu-latest runner got a 404 for `libminizip1t64_1.3.dfsg-3.1ubuntu2.1` from security.ubuntu.com.
Cause: stale apt package lists on the runner image; Ubuntu had pulled the old .deb.
Fix: f7e3174 (test.yml), 85b1be1 (test-coverage.yml) — run `apt-get update` first
Test: none; the CI step itself
Status: fixed

## ISS-7 — `insert --csv` type detection turns a zip code into an int
Symptom: `sqlite-utils insert data.db items items.csv --csv` turned a zip-code column like `02134` into the integer `2134`.
Cause: `ValueTracker.test_integer` (`sqlite_utils/utils.py:470-475`) calls `int(value)`, which succeeds — and silently drops the leading zero — for any all-digit string; `test_integer` has precedence over text in `ValueTracker.guessed_type` (utils.py:487-494). Reached via CLI `insert --csv` without `--no-detect-types` (`cli.py:2192`) → `TypeTracker.wrap()` (utils.py:436-447). Ruled out during investigation: not the `--alter` path (reproduces without it); not SQLite column affinity (value was already a Python `int` before reaching SQLite, confirmed in a debugger).
Fix: uncommitted — not yet fixed.
Test: none yet — next session writes a failing test first (`ValueTracker`/`TypeTracker` in tests/test_utils.py, plus a CLI `insert --csv` test).
Status: open
