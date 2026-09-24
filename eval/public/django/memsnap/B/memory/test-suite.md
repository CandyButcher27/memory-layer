# Test suite and runner

## Purpose
How Django's own tests are organized and run.

## Location
`tests/runtests.py` (entry point), `tests/test_sqlite.py` (default settings),
`tests/requirements/*.txt`, `django/test/` (public test framework used by both Django and users).

## Architecture
- Each top-level directory in `tests/` is a test *app*; `get_test_modules()` discovers them
  (skipping `import_error_package`, `playwright_tests`, `test_runner_apps`; `gis_tests` only when
  GIS is available). Only apps whose tests are selected get added to `INSTALLED_APPS`, on top of
  `ALWAYS_INSTALLED_APPS`.
- `test_sqlite.py` defines two SQLite DBs, `default` and `other` (multi-db tests need both),
  MD5 password hasher for speed, `USE_TZ = False`.
- Runs in a temporary `TMPDIR` (`django_*`). `--parallel` defaults to 0, which becomes "auto" or 1
  depending on the multiprocessing start method and whether the backend can clone test databases.
  Useful flags: `--parallel 1`,
  `--keepdb`, `--failfast`, `-k`, `--tag/--exclude-tag`, `--bisect`, `--pair`, `--shuffle`,
  `--reverse`, `--debug-sql`, `--start-at/--start-after`, `--playwright` (browser tests).
- Test base classes (`django/test/testcases.py`): `SimpleTestCase` (no DB) → `TransactionTestCase`
  (flushes tables) → `TestCase` (wraps each test in a transaction; prefer this).
  `@isolate_apps` (`django/test/utils.py`) for tests that define throwaway models.

## Important Constraints
- Django must be installed in the environment (`pip install -e ..` from `tests/`), otherwise
  `runtests.py` raises `RuntimeError: Django module not found`.
- Models defined in a test module need `app_label` resolvable to a test app, or `@isolate_apps`.

## Testing
`tests/test_runner`, `tests/test_runner_apps`, `tests/test_utils` cover the runner itself.
