# Runtime

## Purpose
Scheduler, memory allocator and GC, stacks, maps, channels, signals, syscalls glue, profiling.

## Location
- `src/runtime/` (~790 files, much of it per-GOOS/GOARCH `.go` and `.s`).
- `src/runtime/HACKING.md` — required reading: G/M/P model, user vs. system stacks,
  `//go:nosplit`, error handling (`throw` vs `fatal` vs `panic`), locking (`mutex`, `note`,
  `gopark`), atomics, and the runtime-only directives (`go:systemstack`, `go:nowritebarrier`,
  `go:nowritebarrierrec`, ...).
- `src/internal/runtime/{atomic,maps,sys,syscall,gc,math,...}` — low-level packages split out of
  the runtime, importable only by the runtime and a few std internals.

## Important Constraints
- Runtime code runs under restrictions ordinary Go does not: no heap allocation or write barriers
  in some contexts, limited stack in nosplit chains, no preemption in others. Per HACKING.md, every
  `//go:nosplit` should say why.
- Its imports are tightly limited by `src/go/build/deps_test.go`.
- Runtime assembly sees `GOEXPERIMENT_x` macros for enabled experiments.

## Testing
`../bin/go test runtime` (long; `-short` helps), plus relevant `test/` files.

## GODEBUG=disablethp
- Declared/parsed like other `GODEBUG` settings in `runtime1.go`: `debug.disablethp` field
  (~line 309) and its `dbgVars` entry (~line 366, no `def`, so default is 0/off).
  Documented in the `//go:debug` block in `extern.go` (~line 77): Linux-only, disables transparent
  huge pages for the heap, kept for compatibility with pre-1.21 behavior (worked around a Linux
  THP default that could balloon RSS, https://go.dev/issue/64332).
- Applied in `mem_linux.go`'s `sysMapOS` (~line 187): after each heap `mmap`, if
  `debug.disablethp != 0` it calls `sysNoHugePageOS(v, n)`, which does
  `madvise(v, n, MADV_NOHUGEPAGE)` (~line 116-123). A few `sysHugePage` call sites for GC metadata
  can still re-enable THP on top of this (comment at mem_linux.go:184-186), i.e. `disablethp=1`
  isn't an absolute guarantee for every mapping.
- Other GOOS have `sysNoHugePageOS`/`sysHugePageOS` stubs (`mem_darwin.go`, `mem_bsd.go`,
  `mem_aix.go`, `mem_windows.go`, `mem_sbrk.go`) but the GODEBUG only has an effect on Linux.
