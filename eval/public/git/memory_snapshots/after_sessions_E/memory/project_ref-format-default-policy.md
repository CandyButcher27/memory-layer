---
name: project_ref-format-default-policy
description: Fork decision to keep REF_STORAGE_FORMAT_FILES as default, not reftable, for this year
metadata:
  type: project
---

Decided 2026-09-23: this fork will not make the reftable ref backend the default in its builds
this year. `git init` must keep producing `.git/refs/` + `packed-refs`, selected by
`REF_STORAGE_FORMAT_DEFAULT` in `repository.h` (gated on `WITH_BREAKING_CHANGES`, currently
`REF_STORAGE_FORMAT_FILES`; see [[refs]]).

**Why:** the org's backup tooling rsyncs `.git/refs/` and `packed-refs` directly. Under reftable,
ref data moves into `.git/reftable/*.ref` tables and there is nothing meaningful under
`.git/refs/`, so that rsync job would silently back up nothing for refs.

**How to apply:** never build this fork with `WITH_BREAKING_CHANGES` defined (upstream ties the
reftable-default switch to that flag for Git 3.0), and don't otherwise force
`init.defaultRefFormat=reftable` in fork-wide config/packaging. Flag any patch that flips this
default or backup tooling that doesn't handle reftable layouts. Revisit if/when the backup
tooling is updated to understand reftable.
