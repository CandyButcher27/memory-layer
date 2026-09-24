# Background tasks (`django.tasks`)

## Purpose
A backend-agnostic API for defining and enqueueing background tasks. Django ships only
development/test backends; real workers come from third-party backends.

## Location
`django/tasks/__init__.py` (backend handler), `base.py` (`Task`, `task` decorator, `TaskResult`,
`TaskResultStatus`, `TaskContext`, `TaskError`), `backends/{base,immediate,dummy}.py`,
`checks.py`, `signals.py`, `exceptions.py`.

## Architecture
- `task_backends` is a `BaseConnectionHandler` over `settings.TASKS` — same alias-keyed pattern as
  `CACHES`/`DATABASES`. `default_task_backend` is a `ConnectionProxy` for the default alias.
- Default setting: `TASKS = {"default": {"BACKEND": "django.tasks.backends.immediate.ImmediateBackend"}}`.
- `@task` wraps a function in a `Task`; `Task.using(...)` returns a modified copy (backend, queue,
  priority, etc.); `enqueue()` / `aenqueue()` hand off to the backend; `call()` runs it directly.
- `BaseTaskBackend.validate_task()` checks the task against backend capabilities before enqueue.
- `ImmediateBackend` runs the task synchronously at enqueue time; `DummyBackend` only stores
  results (useful in tests).

## Testing
`tests/tasks`.
