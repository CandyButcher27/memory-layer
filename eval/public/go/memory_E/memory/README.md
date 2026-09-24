# Project memory index

Component knowledge for the Go main repository. Read the file for the area you're about to
touch; verify against code before relying on it.

| File | Covers | Read before |
|---|---|---|
| [build-bootstrap.md](build-bootstrap.md) | `make.bash`, `cmd/dist`, bootstrap version, `bootstrapDirs` | building the tree; touching `cmd/...` or std packages the toolchain imports |
| [testing.md](testing.md) | `dist test`, `test/` + `cmd/internal/testdir`, codegen asmcheck, `cmd/go` script tests | writing or running tests |
| [compiler.md](compiler.md) | `cmd/compile` phases, SSA rule generation, `types2`→`go/types` generation, GOEXPERIMENT, linker location | compiler, type checker, assembler, linker changes |
| [runtime.md](runtime.md) | runtime layout and its special coding rules (HACKING.md) | any runtime or `internal/runtime` change |
| [go-command.md](go-command.md) | `cmd/go` layout, `alldocs.go` generation, script tests | go command changes |
| [crypto-fips140.md](crypto-fips140.md) | FIPS 140 module, its dependency fence, `lib/fips140` snapshots | crypto changes |
| [api-and-release.md](api-and-release.md) | `api/next`, `doc/next`, `deps_test.go` policy, vendoring | adding exported API or imports; updating `golang.org/x` deps |
| [os-exec-pidfd.md](os-exec-pidfd.md) | Linux pidfd use in `os`/`syscall` process handling and its fallback when `pidfd_open` is unavailable | changes to `os/exec`, `os` process handling, or diagnosing process-handling behavior under seccomp/old kernels |

## Not yet mapped
The standard library packages beyond crypto and os process handling (net, net/http, reflect,
encoding/..., the new `simd` package behind `GOEXPERIMENT=simd`), the linker internals, cgo, and
the `cmd/{trace,pprof,vet,cover}` tools don't have memory files yet. Add one when a session does
real work in that area and learns something a cold session would need.

## When to add a file
Only for a substantial subsystem where reading first would change a future decision. Put small
facts into the closest existing file.
