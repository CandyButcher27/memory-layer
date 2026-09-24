# The go command (cmd/go)

## Purpose
`go build/test/mod/get/list/...`: package loading, module resolution, build cache, toolchain
switching, and invoking compile/link.

## Location
- `src/cmd/go/main.go` — command table; `src/cmd/go/internal/<subsystem>/` —
  `load` (packages), `modload`/`modfetch`/`mvs`/`modget` (modules), `work` (build actions),
  `cache`, `test`, `toolchain` (GOTOOLCHAIN), `fips140`, `vcs`, `web`, etc.
- `src/cmd/go/alldocs.go` — generated `go help` output.
- `src/cmd/go/testdata/script/` — txtar script tests; `testdata/mod/` — fake module proxy
  contents; `testdata/vcstest/` — VCS fixtures.

## Interfaces
- `alldocs.go` is regenerated with `go test cmd/go -run=^TestDocsUpToDate$ -fixdocs`
  (the `//go:generate` in `main.go`). Edit help text in the `internal/*` package, not alldocs.go.
- Script tests: `go test cmd/go -run=Script/^name$`. Script names start with the subcommand or
  concept (`build_`, `mod_`, `vendor_`...).

## Important Constraints
- Most of `cmd/go/internal/...` is in `bootstrapDirs`, so it must compile with Go 1.26
  ([[build-bootstrap]]).
- The `std` and `cmd` modules are special: imports of non-std packages resolve to
  `vendor/...` (see `src/README.vendor`).

## GOTMPDIR
- Read via `cfg.Getenv("GOTMPDIR")` (`src/internal/cfg/cfg.go`), which checks the process env
  then the `go env -w` config file.
- `internal/work.NewBuilder` (`src/cmd/go/internal/work/action.go`) creates the per-invocation
  `$WORK` scratch dir with `os.MkdirTemp(cfg.Getenv("GOTMPDIR"), "go-build")` — this is where
  build/test/install stage compiled packages and binaries, and it's the usual source of "no
  space left on device" when `/tmp` is small (e.g. tmpfs-backed CI runners).
- `testing.T.TempDir()` (`src/testing/testing.go`) reads `GOTMPDIR` independently via
  `os.Getenv`, so `go test` temp dirs created by tests honor it too ([[testing]]).
- `go env -w GOTMPDIR=...` requires an absolute path (empty unsets it); unset falls back to the
  OS default temp dir.
