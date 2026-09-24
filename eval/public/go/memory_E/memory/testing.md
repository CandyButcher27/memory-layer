# Testing infrastructure

## Purpose
How the tree is tested: ordinary package tests, the `test/` black-box suite, compiler codegen
checks, `cmd/go` script tests, and the `dist test` orchestrator.

## Location
- `src/cmd/dist/test.go` — `go tool dist test`, what `run.bash`/`all.bash` execute.
  `registerTests` lists the suite; some packages (e.g. `cmd/internal/testdir`) are registered
  specially but must still pass under plain `go test std cmd`.
- `test/` (repo root) — ~400 entries of toolchain/runtime tests, run by
  `src/cmd/internal/testdir/testdir_test.go`.
- `test/codegen/` — assembly-matching tests (`asmcheck`); see `test/codegen/README`.
- `src/cmd/go/testdata/script/*.txt` — ~940 txtar scripts for the go command; see
  `src/cmd/go/testdata/script/README`.

## Interfaces
- Each `test/*.go` file starts with an action comment: `// run`, `// errorcheck`, `// compile`,
  `// rundir`, `// compiledir`, `// errorcheckdir`, `// asmcheck`, `// build`, `// runoutput`,
  `// skip`, etc. `run` tests compare output against a sibling `.out` file; `errorcheck` tests
  match `// ERROR "regexp"` comments. `*.dir/` directories hold multi-package tests.
- Commands (from `src/`, after `make.bash`):
  - `../bin/go test cmd/internal/testdir -run='Test/(foo.go|bar.go)'`
  - `../bin/go test cmd/internal/testdir -run='Test/codegen' -all_codegen -v` — codegen for all
    architectures (default: host GOARCH only, Linux only). Recommended after compiler changes.
  - testdir flags: `-update_errors`, `-run_skips`, `-target=goos/goarch`, `-shard/-shards`.
  - `../bin/go test cmd/go -run=Script/^name$`
  - `./run.bash --no-rebuild` or `./all.bash` for the full suite.

## Important Constraints
- Standard library tests belong in the package as normal Go tests; add to `test/` only when the
  runner expresses it naturally or it also applies to gccgo (`test/README.md`).
- Tests use the `go` on PATH in several places (compiler tests notably); put `<repo>/bin` first in
  PATH or invoke `../bin/go` explicitly, otherwise you test the wrong toolchain.
- Several tests guard generated files (SSA rewrite rules, `go/types`, `cmd/go/alldocs.go`) and
  policy data (`go/build/deps_test.go`, `cmd/internal/moddeps` for vendoring, `cmd/api`).
