# Manifest parsing, workspace model, and feature gates

## Purpose
Read `Cargo.toml` into Cargo's in-memory model (`Manifest`, `Package`, `Workspace`), validate it,
and gate unstable features.

## Location
- `crates/cargo-util-schemas/src/manifest/mod.rs` — serde TOML schema types (`TomlManifest`,
  `TomlDetailedDependency`, …); `manifest.schema.json` is snapshot-tested from these types
- `src/workspace/parser/mod.rs` — `read_manifest`, TOML → `Manifest` translation, workspace
  inheritance, dependency → `SourceId` (`to_dependency_source_id`); `targets.rs` (target
  discovery), `embedded.rs` (single-file cargo scripts / frontmatter)
- `src/workspace/` — `manifest.rs`, `package.rs`, `workspace.rs` (`Workspace`, member discovery),
  `dependency.rs`, `summary.rs`, `profiles.rs`, `features.rs` (unstable gates), `editor/`
  (`LocalManifest`, used by `cargo add`/`remove`)

## Architecture
- Two layers: schema crate does syntax-level (serde) validation; the parser in
  `src/workspace/parser` does semantic validation and needs feature/context info.
- Some checks run in more than one place (per-package deps, target-specific deps,
  `[workspace.dependencies]` in `workspace.rs`, `[patch]`) — a new dependency field usually
  needs gating in each.

## Unstable features (`src/workspace/features.rs`)
- `cargo-features = [...]` in `Cargo.toml` for manifest syntax; `-Z` flags (`CliUnstable`) for
  CLI/config. Declare with the `features!` macro; check via `features.require(Feature::x())`.
- Choose error / warn / ignore when the gate is missing (rules in the module docs).
- Document in `doc/book/src/reference/unstable.md`; tests use
  `.masquerade_as_nightly_cargo(&["feature"])` and must test the gate itself.

## Builtin dependencies (in progress, unstable `builtin-dependencies`)
`dep = { builtin = true }` for std crates (`core`, `std`, …). Current state:
- Schema: `builtin: bool`, `builtin = false` rejected at deserialize; rejected with
  `workspace = true`.
- Parser rejects combining with `git`/`path`/`registry`/`registry-index`, with a version, and as a
  build-dependency.
- Accepted manifests then hit `todo!("SourceKind::Builtin")` in `to_dependency_source_id` —
  no `SourceKind::Builtin` exists yet. Tests in `tests/testsuite/builtin_dep.rs` snapshot that
  panic, so implementing it will change those expectations.

## Testing
`tests/testsuite/bad_manifest_path.rs`, `inheritable_workspace_fields.rs`, `features*.rs`,
`builtin_dep.rs`; `cargo test -p cargo-util-schemas -F unstable-schema` when schema types change.
