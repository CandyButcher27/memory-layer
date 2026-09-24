# Memory index

Read the file for the subsystem you are about to touch. Each describes how it works now; verify
against the code before relying on a detail.

| File | Covers | Read before touching |
|---|---|---|
| [orm.md](orm.md) | QuerySet → Query → SQLCompiler pipeline, expressions, lookups, fetch modes | `django/db/models/` |
| [migrations.md](migrations.md) | Loader/graph/executor, ProjectState, autodetector, operations, optimizer | `django/db/migrations/`, `makemigrations`/`migrate` |
| [db-backends.md](db-backends.md) | DatabaseWrapper composition, features/ops/schema editor, vendor hooks | `django/db/backends/` |
| [request-handling.md](request-handling.md) | WSGI/ASGI handlers, middleware chain, sync/async adaptation | `django/core/handlers/`, `django/middleware/` |
| [tasks.md](tasks.md) | `django.tasks` background-task API and backends | `django/tasks/` |
| [test-suite.md](test-suite.md) | `tests/runtests.py`, test settings, test case classes | `tests/`, `django/test/` |

## Not yet mapped

Forms, templates, URL resolver internals, `django/contrib/*` (admin, auth, gis, postgres, …),
cache, sessions, management commands, i18n. Add a file when a change window gives you real knowledge
of one of these — don't write one speculatively.

## When to add a file

A subsystem substantial enough that a cold session would make a better decision after reading a
page about it. Small facts go into the closest existing file.
