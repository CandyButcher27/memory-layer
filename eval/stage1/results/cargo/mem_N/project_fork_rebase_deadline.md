---
name: project-fork-rebase-deadline
description: Internal fork must be rebased onto upstream before 2026-10-15 release branch cut
metadata:
  node_type: memory
  type: project
  originSessionId: e8a98360-935a-4635-8b65-66e8a945dc5d
  modified: 2026-09-28T07:23:48.939Z
---

The internal fork must be rebased onto upstream before 2026-10-15 — that's when the release branch gets cut.

**Why:** missing the cut means the fork diverges from the branch that ships, making future rebases harder.

**How to apply:** Flag any rebase-related work as time-sensitive as 2026-10-15 approaches; prioritize resolving conflicts/upstream drift over other work if the deadline is close.
