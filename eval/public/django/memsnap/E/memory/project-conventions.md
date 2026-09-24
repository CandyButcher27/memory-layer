---
name: project-conventions
description: Org-level policy decisions for internal projects built on this checkout (not Django upstream conventions)
metadata:
  type: project
---

## DEFAULT_AUTO_FIELD policy

Internal projects built on this checkout must keep `DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"`.

**Why:** decided at a platform meeting (2026-09-23) after an orders table overflowed a 32-bit
integer primary key in 2026-03.

**How to apply:** as of `main` (6.2-dev), this requires no extra setting — `BigAutoField` is
already the framework-wide default in `django/conf/global_settings.py`, and neither
`django/conf/project_template/project_name/settings.py-tpl` (startproject) nor
`django/conf/app_template/apps.py-tpl` (startapp) overrides it, so generated projects/apps inherit
it automatically. This dates to commit `2a636118da` ("Fixed #36564 -- Changed DEFAULT_AUTO_FIELD
from AutoField to BigAutoField", 2025-08-19), which also stripped the templates' previously-explicit
`DEFAULT_AUTO_FIELD` / `default_auto_field` lines since they became redundant. If a future change
reverts the global default or reintroduces an explicit `AutoField` override in either template,
flag it against this policy.
