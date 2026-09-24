# Package sources

## Purpose
Provide package metadata (`Summary`) and contents to the resolver and downloader.

## Location
- `src/sources/source.rs` — `Source` trait, `SourceMap`
- `src/sources/registry/` — `RegistrySource` over `RegistryData` impls: `local.rs`,
  `git_remote.rs` (`GitRegistry`), `http_remote.rs` (`HttpRegistry`, sparse; default since 1.70),
  `index/`, `download.rs`
- `src/sources/git/` — `GitSource`; `utils.rs` (libgit2), `oxide.rs` (gitoxide),
  `known_hosts.rs` (CVE-2022-46176 host-key checking)
- `src/sources/path.rs`, `directory.rs` (vendored), `replaced.rs` + `config.rs`
  (`SourceConfigMap`, `[source.*]` replacement), `overlay.rs`
- `src/workspace/source_id.rs` — `SourceId`, unique identity of a source; the `SourceKind` enum
  itself lives in `crates/cargo-util-schemas/src/core/source_kind.rs`
- Credentials/auth: `src/util/auth/`, `src/util/credential/`, `credential/*` crates
- Network helpers: `src/util/network/`

## Important constraints
- `$CARGO_HOME/registry` access requires manually acquiring the package cache lock
  (`GlobalContext::acquire_package_cache_lock`).
- A new `SourceKind` (e.g. `Builtin`, see [[manifest-and-workspace]]) touches `SourceId`
  encoding, lockfile encoding, and every `match` on source kind.

## Testing
`tests/testsuite/registry*.rs`, `git*.rs`, `alt_registry.rs`, `vendor.rs`, `source_replacement.rs`;
fixtures via `cargo_test_support::registry` and `::git`. Git/SSH container tests need
`CARGO_CONTAINER_TESTS=1`.
