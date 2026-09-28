---
name: feedback-no-replace-use-upsert-with-pk
description: Never use --replace in production; always use --upsert with explicit --pk instead
metadata:
  node_type: memory
  type: feedback
  originSessionId: da8b08c6-aaf6-4fc5-831d-dd8bb9d46cc7
  modified: 2026-09-28T08:13:22.712Z
---

Never suggest or use `sqlite-utils ... --replace` in production. Always use `--upsert` together with an explicit `--pk`.

**Why:** `--replace` does `INSERT OR REPLACE`, which deletes and reinserts the whole row on a primary-key conflict — this once wiped out the user's enrichment columns that weren't present in the incoming record. `--upsert` instead does `INSERT ... ON CONFLICT(pk) DO UPDATE SET col = excluded.col` for only the columns present in the incoming record, leaving other columns (like enrichment columns) untouched.

**How to apply:** When writing or reviewing any sqlite-utils insert command for this project's production data, use `--upsert --pk <col>` and never `--replace`. Flag `--replace` if seen in a script or PR touching production data.
