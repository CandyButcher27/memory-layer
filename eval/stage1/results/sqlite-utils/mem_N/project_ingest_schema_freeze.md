---
name: ingest-schema-freeze
description: Ingest database schema freeze date is 2026-11-01
metadata:
  node_type: memory
  type: project
  originSessionId: 0fadaf75-96bb-4f0a-9e17-b66030d4c138
  modified: 2026-09-28T08:14:37.249Z
---

The ingest database's schema freeze is 2026-11-01. No schema changes (new columns, table structure, migrations) to the ingest database should land after that date without checking in first.

**Why:** Stated as a hard freeze date for the ingest database.

**How to apply:** Flag any proposed schema change to the ingest database scheduled on/after 2026-11-01, and suggest landing before the freeze instead.
