# CLAUDE.md

This is the main Go repository (`module std` at `src/go.mod`, currently `go 1.28` development).
It contains the toolchain (`src/cmd/...`), the runtime, the standard library, the black-box test
suite (`test/`), API compatibility data (`api/`), and release notes (`doc/next/`).

## Working here

- **Build the tree before testing.** There is no `bin/go` until you run `cd src && ./make.bash`
  (needs a bootstrap Go ≥ 1.26.0 via `GOROOT_BOOTSTRAP` or `go` on `PATH`). Then use
  `../bin/go` (from `src/`) — not the system `go` — for everything: tests run against the tree's
  own toolchain. See `memory/build-bootstrap.md`.
- **Test narrowly first**, then broaden: `../bin/go test <pkg>`; toolchain changes also need
  `../bin/go test cmd/internal/testdir` (the `test/` directory). `./all.bash` is the full gate.
  See `memory/testing.md`.
- **Generated files are never hand-edited.** Edit the source and regenerate: SSA rules
  (`cmd/compile/internal/ssa/_gen`), `go/types` (generated from `cmd/compile/internal/types2`),
  `cmd/go/alldocs.go`, `internal/goexperiment/exp_*.go`. A test fails when they are stale.
- **Policy data is not a build fix.** Do not relax `src/go/build/deps_test.go` rules or
  `crypto/internal/fips140deps.AllowedInternalPackages` to make a build pass.
- **New exported API** needs an `api/next/<issue>.txt` line and a matching
  `doc/next/*stdlib/*minor/<pkg>/<issue>.md` note. See `memory/api-and-release.md`.
- **Vendored code** (`src/vendor`, `src/cmd/vendor`) is updated only via `go get` +
  `go mod vendor`, never edited in place.
- **Commit messages** follow `pkg/path: lowercase summary` (or `all:` for tree-wide), a wrapped
  body explaining why, and `Fixes #N` / `Updates #N`. Changes go through Gerrit
  (go-review.googlesource.com), not GitHub PRs.

## Workflow

- `/think` — for non-obvious design work, use it before committing to an approach
- Before substantial work, read `memory/README.md` and the relevant `memory/*.md`, then inspect
  the actual code before trusting what memory says. Code is the source of truth.

## Maintaining project memory

After every major change window — a feature, a significant bug fix, an
architecture/API/pipeline/dependency change, a substantial refactor, or a completed debugging
investigation (not a trivial edit):

- update the affected `memory/*.md` files;
- create a new memory file when a new substantial subsystem appears;
- update `memory/README.md` whenever memory files are added, renamed, merged, or removed;
- correct stale claims in place rather than adding a new fact beside a contradictory old one.

Never reference `memory/` in commits, CL descriptions, code comments, or other external output —
state the underlying project fact instead.
