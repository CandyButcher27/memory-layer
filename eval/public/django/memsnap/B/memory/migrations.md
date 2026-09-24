# Migrations framework

## Purpose
Detect model changes (`makemigrations`), write migration files, and apply/unapply them (`migrate`).

## Location
`django/db/migrations/`: `loader.py`, `graph.py`, `executor.py`, `recorder.py`, `state.py`,
`autodetector.py`, `questioner.py`, `optimizer.py`, `writer.py`, `serializer.py`,
`operations/{base,models,fields,special}.py`. Commands in `django/core/management/commands/`.

## Architecture
- **MigrationLoader** reads migration modules from disk + applied rows (`MigrationRecorder`, table
  `django_migrations`) and builds a **MigrationGraph** of dependencies.
- **MigrationExecutor** (`executor.py`) computes `migration_plan(targets)` as
  `(Migration, backwards?)` pairs and runs each migration's operations inside a schema editor.
- **ProjectState / ModelState** (`state.py`) is the historical model state. Operations never touch
  real models; `ProjectState.apps` renders a `StateApps` registry of fake historical models.
  `reload_model(s)` re-renders only affected models (and related ones) for speed.
- **Operation** contract (`operations/base.py`): `state_forwards()` mutates state;
  `database_forwards/backwards(app_label, schema_editor, from_state, to_state)` issue DDL;
  `describe()` / `migration_name_fragment` for naming; `reduce()` for optimization.
- **MigrationAutodetector.changes()** diffs two ProjectStates (`_detect_changes`), then
  `arrange_for_graph()` names/numbers them against the existing graph.
- **MigrationOptimizer** repeatedly calls `reduce()` pairwise, scanning forward over operations it
  can optimize through, until the list stops changing; result must be equal or shorter.
- **MigrationWriter / serializer** turn operations back into Python source; any new value type in
  field/operation kwargs needs a serializer.

## Important Constraints
- Historical models only carry what `ModelState` captures — no custom methods. Data migrations must
  use `apps.get_model()`.
- Changing an operation's `deconstruct()` or the autodetector output affects every user project's
  generated migrations. CI (`.github/workflows/check-migrations.yml` → `scripts/check_migrations.py`)
  installs every test app plus contrib and runs `makemigrations --check` on PostgreSQL, so a model
  change in contrib or a test app without its migration fails CI.

## Testing
`tests/migrations` (autodetector, operations, optimizer, writer, executor, loader),
`tests/migrations2`, `tests/migrate_signals`, `tests/schema` for the DDL side.
