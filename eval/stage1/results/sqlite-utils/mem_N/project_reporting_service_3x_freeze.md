---
name: reporting-service-3x-freeze
description: Reporting service stays on sqlite-utils 3.x API until Q1 2027 due to dependency on old upsert behavior
metadata:
  node_type: memory
  type: project
  originSessionId: 0fadaf75-96bb-4f0a-9e17-b66030d4c138
  modified: 2026-09-28T08:14:15.980Z
---

The reporting service stays on the sqlite-utils 3.x API until Q1 2027, because the dashboard team's code depends on the old upsert behavior (pre-4.0 `INSERT OR IGNORE` + `UPDATE` semantics, rather than 4.0's `INSERT ... ON CONFLICT ... DO UPDATE SET`).

**Why:** Dashboard team's code was written against 3.x upsert semantics and hasn't been ported.

**How to apply:** Don't suggest upgrading the reporting service to sqlite-utils 4.x, or relying on 4.x-only upsert behavior (e.g. automatic `PrimaryKeyRequired`, no `pk=` needed) for that service, before Q1 2027. If they need to move sooner, note that `Database(..., use_old_upsert=True)` restores the 3.x upsert SQL under 4.x — see changelog/upgrading docs (`upgrading_3_to_4`). Related: [[feedback_no_replace_use_upsert_with_pk]].
