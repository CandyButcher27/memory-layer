# Resolver and lockfile

## Purpose
Pick exact package versions and features for a workspace, and load/save `Cargo.lock`.

## Location
- `src/ops/resolve.rs` — high-level API: `resolve_ws` (no options), `resolve_ws_with_opts`
  (usual choice), `resolve_with_previous` (low-level; honors an existing lock / `[patch]`)
- `src/resolver/` — core algorithm (`mod.rs`, `context.rs`, `dep_cache.rs`,
  `conflict_cache.rs`, `version_prefs.rs`), `features.rs` (feature resolver v2),
  `encode.rs` (`Cargo.lock` format, `ResolveVersion`), `errors.rs`
- `src/ops/lockfile.rs` — `load_pkg_lockfile` / `write_pkg_lockfile`
- `src/workspace/registry.rs` — `PackageRegistry`, what the resolver queries (handles `[patch]`)
- `crates/resolver-tests` — property/SAT-based tests for the resolver

## Architecture
- Backtracking DFS that tries the highest compatible version first; one semver-compatible
  version per crate, unique `links`. Performance-critical — avoid allocation in hot paths.
- Resolution runs with all features for the lockfile; the separate feature resolver
  (`resolver::features`) then *narrows* features per build (host/target/dev unification
  options in `FeatureOpts`). Anything asking "is feature X enabled" must use the feature
  resolver's result, not the dependency resolver's.

## Important constraints
- Lockfile format changes follow a slow rollout (`encode.rs` docs): add a new `ResolveVersion`,
  preserve it when found, and only change `ResolveVersion::default()` after it has been on stable
  for a while. Test in `tests/testsuite/lockfile_compat.rs`.

## Testing
`tests/testsuite/` (e.g. `features*.rs`, `patch.rs`, `update.rs`, `lockfile_compat.rs`),
`cargo test -p resolver-tests`.
