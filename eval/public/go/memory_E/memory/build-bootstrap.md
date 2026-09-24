# Build and bootstrap (make.bash, cmd/dist)

## Purpose
Builds the Go toolchain and standard library from source using an older Go release.

## Location
- `src/make.bash` (`.bat`, `.rc`) — entry point; must be run from `src/`.
- `src/all.bash` — `make.bash` then `run.bash --no-rebuild` then `dist banner`.
- `src/run.bash` — runs `go tool dist test`; requires `../bin/go` to exist.
- `src/cmd/dist/` — the bootstrap tool (`build.go`, `buildtool.go`, `test.go`, `README`).
- Outputs: `bin/` (go, gofmt), `pkg/tool/<goos>_<goarch>/` (compile, link, asm, ...),
  `pkg/bootstrap/` (scratch workspace). All are gitignored.

## Architecture
Bootstrap sequence (`cmd/dist/README`):
1. Build `cmd/dist` with the bootstrap Go (minimum `go1.26.0`, `minBootstrap` in
   `buildtool.go`; `bootgo=1.26.0` in `make.bash`).
2. dist builds toolchain1 + `go_bootstrap` with the bootstrap Go.
3. `go_bootstrap` rebuilds the toolchain with itself.
4. `go_bootstrap` builds the rest of std and cmd.

Step 2 copies every directory in `bootstrapDirs` (`buildtool.go`) into `$GOROOT/pkg/bootstrap`,
rewriting imports to `bootstrap/<path>` (and `cmd/vendor/X` to `bootstrap/X`).

## Important Constraints
- **Anything in `bootstrapDirs` must compile with the minimum bootstrap Go (1.26).** That covers
  `cmd/compile/...`, `cmd/link/...`, `cmd/asm`, `cmd/cgo`, most of `cmd/go/internal/...`,
  `cmd/internal/...`, and some std packages (`go/constant`, `internal/abi`, `internal/buildcfg`,
  ...). Don't use language features or std APIs newer than the bootstrap in those packages.
  The required bootstrap version is derived from the `go` line in `go.mod` by
  `requiredBootstrapVersion` (`build.go`); the rationale is go.dev/issue/54265.
- `notgo126.go` exists only to give a clear error when dist is built with too-old Go.
- `GOROOT_BOOTSTRAP` picks the bootstrap; otherwise `$HOME/go1.26.0`, `$HOME/sdk/go1.26.0`,
  `$HOME/go1.4`, or `go env GOROOT` of a `go` on PATH.

## Configuration
Env vars documented at the top of `make.bash`: `GOHOSTARCH`, `GOARCH`, `GOOS`, `GO_GCFLAGS`,
`GO_LDFLAGS`, `CGO_ENABLED`, `CC`/`CC_FOR_TARGET`, `GOEXPERIMENT` (sets default experiments baked
into the toolchain). `go.env` at the repo root holds default `GOPROXY`, `GOSUMDB`, `GOTOOLCHAIN`.

## `make.bash` is always a cold build — there's no warm-cache variant
`cmdbootstrap()` (`build.go`) points `GOCACHE` at `$GOROOT/pkg/obj/go-build`, and `setup()`
registers an `xatexit` hook (build.go ~592-597) that `xremoveall`s that whole directory when the
`dist` process exits — see the comment at build.go ~963-965: "Use a build cache separate from the
default user one. Also one that will be wiped out during startup, so that make.bash really does
start from a clean slate." So the cache from run N is gone before run N+1 starts; repeated
`./make.bash` runs on an unchanged tree should time the same (mod machine noise), because every
run *is* the cold-cache case by design. `GOPROXY=off` is also set for the whole bootstrap
(build.go ~961), so there's no network/module-download variance either. To get an actual
warm-cache comparison, benchmark `../bin/go install std cmd` (ordinary persistent `GOCACHE`)
after the toolchain is already built, not repeated `make.bash` invocations.

## Testing
`go test cmd/dist` (e.g. `build_test.go` checks `requiredBootstrapVersion`).
