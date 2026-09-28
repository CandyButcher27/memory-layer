---
name: project-sample-option-rows
description: "--sample N option for sqlite-utils rows — implementation approach and CLI constraint"
metadata:
  node_type: memory
  type: project
  originSessionId: d5922232-94ab-432a-bf63-d1e2f129e927
  modified: 2026-09-28T08:15:51.507Z
---

Adding `--sample N` to `sqlite-utils rows` (random N rows). Step 1 done: `Table.rows_where()` in `sqlite_utils/db.py` now takes a keyword-only `sample: int | None = None`, implemented as `order by random() limit N`, and raises `ValueError` if combined with `order_by`/`limit`/`offset`. Step 2 (CLI wiring in `sqlite_utils/cli.py`), tests, and docs are still pending — user plans to resume "tomorrow" (next session after 2026-09-28).

**Why:** User already tried a random-offset approach (`offset abs(random()) % count`) last week and rejected it — it returns duplicate rows and doesn't work for WITHOUT ROWID tables. `order by random() limit N` is the deliberate, validated choice.

**How to apply:** Don't suggest or reintroduce the offset-based random sampling approach. When wiring the `--sample` CLI flag, make it mutually exclusive with `--order` (error if both given) — user explicitly requested this constraint for step 2.
