# API compatibility, release notes, dependency policy, vendoring

## Purpose
Process data that CI checks on almost every std change.

## Location and rules
- **`api/`** — data for `cmd/api` (`api/README`). `go1.N.txt` files are frozen once shipped.
  New exported API goes into `api/next/<proposal-issue>.txt`, one feature per line, each ending in
  `#<issue>`. `except.txt` lists features allowed to disappear.
- **`doc/next/`** — release notes for the in-progress release (`doc/README.md`). Every
  `api/next/NNNNN.txt` needs `doc/next/6-stdlib/99-minor/<pkg/path>/NNNNN.md` (at least a
  sentence or a TODO). Don't use `RELNOTE=yes` in commit messages. Link issues as
  `/issue/NNNNN`, symbols as `[pkg.Symbol]`. `doc/initial/` seeds the next cycle.
- **`src/go/build/deps_test.go`** — `depsRules`, the policy for which std packages may import
  which. "DO NOT CHANGE THIS DATA TO FIX BUILDS"; negative assertions are almost never removed.
  A new import in a low-level package that fails this test needs discussion, not a rule edit.
- **Vendoring** (`src/README.vendor`) — `src/vendor` and `src/cmd/vendor` for modules `std`
  (`src/go.mod`) and `cmd` (`src/cmd/go.mod`). Update with
  `go get <mod>@<ver> && go mod tidy && go mod vendor` from `src/` or `src/cmd` using the tree's
  own `go`, then `go test cmd/internal/moddeps`. Commits are titled `all: update to x/...@<rev>`.

## Why
The Go 1 compatibility promise: shipped API can't be removed, so additions are audited per
proposal issue at the end of each cycle.
