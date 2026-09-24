# CLAUDE.md

Django itself — the framework source, not a Django project. `main` is the 6.2 development
branch (`django/__init__.py`: `VERSION = (6, 2, 0, "alpha", 0)`), Python >= 3.12.

## Layout

- `django/` — the framework package (ORM in `django/db/`, request handling in `django/core/handlers/`,
  `django/tasks/` background tasks, `django/contrib/` bundled apps).
- `tests/` — the test suite: ~220 top-level test apps run by `tests/runtests.py`, not pytest.
- `docs/` — Sphinx docs; `docs/releases/A.B.txt` holds release notes.
- `js_tests/` — QUnit tests for admin JavaScript (run via `Gruntfile.js` / `package.json`).

## Commands

```bash
python -m pip install -e . && python -m pip install -r tests/requirements/py3.txt
cd tests && ./runtests.py                          # full suite, SQLite (settings: test_sqlite)
cd tests && ./runtests.py basic queries.test_q     # app labels or dotted paths
cd tests && ./runtests.py --settings=test_postgres  # other DBs need a settings module you write
tox -e black,flake8,isort,docs                     # linters (also in .pre-commit-config.yaml)
```

`runtests.py` raises `Django module not found` unless Django is pip-installed (editable) into the
active environment.

## Conventions

- Code style: black (line length 88), isort profile black, flake8 with `max-doc-length = 79`.
- Commit messages: `Fixed #NNNNN -- Past-tense summary.` or `Refs #NNNNN -- ...`; backports to
  `stable/A.B.x` are prefixed `[A.B.x]` (enforced by `.github/workflows/check_commit_messages.yml`).
- New features / behavior changes need a release note in `docs/releases/6.2.txt` and
  `.. versionadded:: 6.2` / `.. versionchanged:: 6.2` in the reference docs.
- Deprecations use `RemovedInDjango2028Warning` / `RemovedInDjango2029Warning`
  (`django/utils/deprecation.py`); mark removal sites with a `# RemovedInDjango20XXWarning:` comment.
- Bug fixes come with a regression test in the relevant `tests/<app>/` directory.

## Workflow

- `/think` — for non-obvious design work, use it before committing to an approach
- Before substantial work: read `memory/README.md` and the relevant `memory/*.md`, then inspect the
  actual code before trusting memory — the code is the source of truth.
- After every major change window (a feature, a significant bug fix, an
  architecture/API/pipeline/dependency change, a substantial refactor, a completed debugging
  investigation — not a trivial edit): update the affected `memory/*.md`; create a new memory file
  for a new substantial subsystem; update `memory/README.md`; correct stale claims in place rather
  than leaving them beside new ones.
- Never mention `memory/` in commits, PRs, code comments, or docs — state the underlying fact.
