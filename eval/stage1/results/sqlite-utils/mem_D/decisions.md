# Decisions
<!-- One short entry per choice someone might argue again:
"## DEC-<n> — <choice>" heading, then
Why:
Rejected: <alternative> — <reason>
Reverse if: <condition that would change the answer>
Date:
Never edit an old entry's reasoning. Add a new one and mark the old "Superseded by DEC-<m>". -->

## DEC-1 — Database context manager rolls back on exit instead of committing
Why: exit equals `close()`. Every library write commits itself, so an open transaction at exit was opened by the caller; auto-committing could persist half-finished work (e.g. early return). Commit 6c88067, documented in docs/python-api.rst.
Rejected: commit on success like `sqlite3.Connection`'s context manager — silently persists partial work.
Reverse if: library methods stop committing their own writes.
Date: 2026-07-04

## DEC-2 — Database() rejects Python 3.12+ autocommit= connections
Why: with `autocommit=True` `commit()` is a no-op, and `autocommit=False` connections are always in a transaction; in both modes library writes looked fine in-process but were discarded on close. Raising `TransactionError` beats silent data loss. Commit bcd9a26.
Rejected: accepting them — silent data loss.
Reverse if: the library gains a transaction model that works with sqlite3's `autocommit` attribute.
Date: 2026-07-04

## DEC-3 — `rows_where(sample=N)` uses `order by random() limit N`, not random-offset
Why: user tried a random-offset approach (`offset abs(random()) % count`, applied per row) the week of 2026-09-21; it returned duplicate rows and doesn't work for WITHOUT ROWID tables. `order by random() limit N` has neither problem. Implemented in `sqlite_utils/db.py` `Queryable.rows_where()` (uncommitted as of this session); `sample` is keyword-only, raises `ValueError` if combined with `order_by`/`limit`/`offset`.
Rejected: `offset abs(random()) % count` per-row sampling — duplicate rows, breaks on WITHOUT ROWID tables.
Reverse if: a future SQLite version makes `order by random()` too slow on large tables and a better sampling primitive becomes available.
Date: 2026-09-28
