---
name: no-spatialite-in-prod
description: "SpatiaLite extension can't ship in production due to Lambda layer size limit"
metadata:
  node_type: memory
  type: project
  originSessionId: 0fadaf75-96bb-4f0a-9e17-b66030d4c138
  modified: 2026-09-28T08:14:40.614Z
---

The SpatiaLite SQLite extension cannot be shipped in production because it would exceed the Lambda layer size limit.

**Why:** AWS Lambda layer size constraint, not a functionality/compatibility issue.

**How to apply:** Don't suggest adding SpatiaLite (`find_spatialite()`, GIS features) to the production Lambda deployment. GIS/SpatiaLite work is fine for local/dev/test use, just not the prod Lambda path.
