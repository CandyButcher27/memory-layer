# Compilation pipeline

## Purpose
Turn a resolved workspace into rustc/rustdoc invocations and build-script runs, skipping
up-to-date work. Backs `build`, `check`, `test`, `bench`, `doc`, `rustc`, `rustdoc`, `run`, `install`.

## Location
- `src/ops/cargo_compile/` — entry point `compile`; `unit_generator.rs` (root units from CLI
  target selection), `compile_filter.rs`, `packages.rs`
- `src/compiler/` — everything that talks to rustc
  - `build_context/` (`BuildContext`, `target_info.rs` queries rustc for target cfg/file types)
  - `unit.rs`, `unit_dependencies.rs` (lower package `Resolve` to a `Unit` graph), `unit_graph.rs`
  - `build_runner/` (`BuildRunner`; `compilation_files.rs` computes output names/metadata hashes)
  - `job_queue/` (parallel scheduling, jobserver, messages)
  - `fingerprint/` (freshness), `custom_build.rs` (build scripts), `layout.rs` (`target/` dirs)
  - `standard_lib.rs` (`-Zbuild-std`), `timings/`, `output_sbom.rs`, `unused_deps.rs`

## Architecture
1. Resolve (`ops::resolve_ws_with_opts`) and download (`PackageSet`).
2. Generate root units, then walk the resolve to build the `UnitGraph`.
3. `BuildContext` = the immutable "front end" result.
4. `BuildRunner` prepares `Layout`, builds a `JobQueue`; each unit's fingerprint decides
   dirty vs fresh; `drain_the_queue` runs leaves until empty. This is the only place Cargo uses
   threads.
5. Result is a `Compilation` (used e.g. by `cargo test` to run binaries).

"Target" in this code usually means a Cargo target (lib/bin/test/…), not a target triple.

## Important constraints
- Fingerprints must never hash mtimes or absolute paths: Docker zeroes nanosecond mtimes, and
  renaming a project dir must keep the cache valid. Hash relative paths; the root is supplied at
  runtime. (`fingerprint/mod.rs` "Considerations for inclusion in a fingerprint".)
- Registry deps don't track file mtimes (a new version changes the `PackageId`).
- Build-script run units have their own fingerprint (`calculate_run_custom_build`): with no
  `rerun-if-*` directives any file change in the package reruns it; otherwise only listed items.
- Changing how output filenames/metadata hashes are computed is gated by `METADATA_VERSION`
  in `build_runner/compilation_files.rs` — bump it deliberately, as it invalidates every cache.
- `fingerprint/mod.rs` has a table of what each input affects (fingerprint vs metadata hash);
  update it when adding a new compiler input.

## Testing
`tests/testsuite/freshness*.rs`, `build*.rs`, `build_script*.rs`, `build_dir*.rs`,
`build-std` tests (`tests/build-std`, nightly + `CARGO_RUN_BUILD_STD_TESTS=1`).

## `cargo test`/`cargo bench` binary spawning (verified 2026-09-24)
- `src/ops/cargo_test.rs`: `run_tests`/`run_benches` call `compile_tests` → `ops::compile` (full
  `JobQueue::drain_the_queue`, see Architecture above) and only *after* it returns do they iterate
  `compilation.tests` and spawn each test executable via `cmd_builds` → `compilation.target_process`
  → `ProcessBuilder::exec` (`run_unit_tests`, sequential, one `cmd.exec()` per unit, no parallelism
  and no retry/backoff around the spawn).
- `ProcessBuilder::exec`/`_status` (`crates/cargo-util/src/process_builder.rs`) call
  `std::process::Command::spawn()` directly; the only retry there is `should_retry_with_argfile`
  (for "command line too long" errors), not for spawn failures like access-denied.
- The executable itself reaches `target/<profile>/deps/...` via `link_targets` in
  `src/compiler/mod.rs` (`paths::link_or_copy`), run as a `Work` closure inside the same job queue,
  right after the linking rustc process for that unit exits — so on Windows there's no cargo-side
  delay between a linker process closing the new `.exe` and a later `cargo test` invocation trying
  to spawn it; anything that transiently locks freshly-written `.exe` files (e.g. an AV scanner)
  has no cargo-side wait/retry to absorb it today.

## Building this workspace itself
The root `Cargo.toml` has no `[profile.release]` table (verified 2026-09-24; only unrelated
`[profile]` tables live in `tests/testsuite/cargo_remove/*_profile/{in,out}/Cargo.toml` fixtures),
and `.cargo/config.toml` sets no `rustflags`. So `cargo build --release` here just uses Cargo's
built-in release defaults (`opt-level = 3`, `codegen-units = 16`, `lto = false`, `debug = false`).
A multi-minute release build time is expected from `opt-level = 3` codegen across the dependency
tree (curl, git2, gix, openssl-src, rusqlite bundled, etc.), not from profile misconfiguration —
don't assume a slow build points at a profile setting without checking for one first.
