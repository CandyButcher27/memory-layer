# Build performance (make.bash / cmd/dist)

Last verified: 2026-09-24

## make.bash has no cold-vs-warm cache distinction
`dist bootstrap` uses a GOCACHE isolated inside the tree (`$GOROOT/pkg/obj/go-build`,
set at src/cmd/dist/build.go:967), not the user's normal build cache. `make.bash` always
invokes `dist bootstrap -a` (src/make.bash:219), which sets `rebuildall=true`
(src/cmd/dist/build.go:928 flag binding). With `rebuildall` true, `setup()` removes
`pkg/obj/go-build` before the build starts (build.go:593-594) and an `xatexit` hook
removes it again after the build finishes (build.go:597), regardless of exit status.
The three `goInstall` calls that build the toolchain (toolchain3, toolchainGOEXPERIMENT,
toolchainTarget; build.go:1085,1099,1139) also pass `-a` explicitly; toolchain2
(build.go:1056) doesn't need to since the cache dir is already empty.
Net effect: every `make.bash` run does a full rebuild of the compiler/stdlib from
nothing — there's no warm-cache state to compare against. A run that looks slower isn't
explained by cache temperature; look at CPU contention, GOMAXPROCS, or GOROOT_BOOTSTRAP
toolchain version instead.
Measured: 32-core build box, 5 runs, median 2m41s, 2026-09-20 (source: user report, not
independently re-measured here).
