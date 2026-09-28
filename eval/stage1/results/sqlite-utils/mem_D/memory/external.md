# External systems
<!-- Only what the code cannot tell you: provider quirks, deferred constraints, what the deploy runs,
which credentials reach what, environment traps. Move a topic to its own file once it passes ~40 lines. -->

Last verified: 2026-09-28

## Test fails only on the old-SQLite CI job (sqlite_schema, RETURNING, UPSERT)
`.github/workflows/test-sqlite-support.yml` runs the suite against SQLite 3.46 and 3.23.1 (2018, before UPSERT).
- Use `sqlite_master`, not `sqlite_schema`, in SQL and tests (b432e68).
- `RETURNING` needs SQLite 3.35+; tests using it must skip below that (2582446).

## Code imports a package that is only in the dev dependency group
Runtime deps are `[project] dependencies` in pyproject.toml; `typing_extensions` and the linters come only from the `dev` group. Importing one at runtime crashed 4.2 (ISSUES.md ISS-1). Check with `just test-no-dev-dependencies`.

## sqlite-utils-geo plugin issues go to Dmitri
Internal plugin, maintained by Dmitri (not in this repo). Discovered via pluggy setuptools entrypoints (`sqlite_utils/plugins.py`); hooks it can implement are in `sqlite_utils/hookspecs.py`.

## Reporting service stays on the 3.x upsert behaviour until Q1 2027
The dashboard team's code depends on the pre-4.0 upsert (`INSERT OR IGNORE` + `UPDATE`), not the 4.0 `INSERT ... ON CONFLICT ... DO UPDATE SET` rewrite (docs/upgrading.rst, "Upserts use INSERT ... ON CONFLICT"). Until they migrate, point them at `Database(..., use_old_upsert=True)` (docs/python-api.rst, `python_api_old_upsert`) rather than changing shared upsert code.

## Ingest database schema freeze 2026-11-01
No schema changes to the ingest database after this date (told 2026-09-28).

## SpatiaLite can't ship in production (Lambda layer size limit)
`find_spatialite()` (sqlite_utils/utils.py) only checks local install paths (apt/homebrew/`/usr/local/lib`) — none of them are a Lambda layer path, so this isn't something the code would surface. Told 2026-09-28.
