---
name: feedback-resolver-review
description: Changes touching the resolver (src/resolver/) require a second reviewer from the platform team
metadata:
  node_type: memory
  type: feedback
  originSessionId: e8a98360-935a-4635-8b65-66e8a945dc5d
  modified: 2026-09-28T07:23:52.018Z
---

Any change touching the resolver (`src/resolver/`) needs a second reviewer from the platform team, in addition to normal review.

**Why:** resolver changes have wide blast radius across dependency resolution behavior.

**How to apply:** When proposing or preparing PRs that modify `src/resolver/`, remind the user to loop in a platform team reviewer before merging.
