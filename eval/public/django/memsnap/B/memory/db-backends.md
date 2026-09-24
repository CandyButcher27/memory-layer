# Database backends

## Purpose
Adapt the ORM and migrations to SQLite, PostgreSQL, MySQL/MariaDB, and Oracle.

## Location
`django/db/backends/base/` defines the abstract pieces; each of `sqlite3/`, `postgresql/`,
`mysql/`, `oracle/` subclasses them. `dummy/` is the unconfigured placeholder. GIS backends live in
`django/contrib/gis/db/backends/`.

## Architecture
`BaseDatabaseWrapper` (`base/base.py`) composes per-backend classes named by attributes:
`client_class`, `creation_class`, `features_class`, `introspection_class`, `ops_class`,
`validation_class`, and `SchemaEditorClass`.

- **features** (`DatabaseFeatures`) — boolean/capability flags (`supports_*`, `has_*`,
  `can_*`), `minimum_database_version`, and test skips/expected failures.
- **ops** (`DatabaseOperations`) — SQL fragments and value adaptation; `compiler_module` selects the
  SQL compiler module (see [[orm]]).
- **schema** (`BaseDatabaseSchemaEditor`, ~2100 lines) — DDL for migrations. SQLite's editor
  remakes tables for most ALTERs because SQLite's ALTER TABLE is limited.
- **creation** — test database create/destroy/clone (used by `--parallel` and `--keepdb`).

## Configuration
Minimum versions (from each `features.py`): SQLite 3.37, PostgreSQL 16, MySQL 8.4, MariaDB 10.11,
Oracle 19.

## Important Constraints
- Gate behavior on a feature flag, not on `connection.vendor`, so third-party backends can opt in.
- Tests that need a capability use `@skipUnlessDBFeature` / `@skipIfDBFeature`.
- Per-vendor SQL for an expression goes in an `as_<vendor>()` method on the expression.

## Testing
`tests/backends/` (with per-vendor subdirs), `tests/schema`, `tests/introspection`,
`tests/inspectdb`. Non-SQLite backends need a settings module passed via `--settings`.
