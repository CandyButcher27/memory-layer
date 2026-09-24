# Configuration (`GlobalContext`)

## Purpose
Global environment and configuration: `.cargo/config.toml` hierarchy, `CARGO_*` env vars,
`--config` CLI args, shell, home dirs, caches, locks.

## Location
- `src/context/` — `mod.rs` (`GlobalContext`), `value.rs` / `config_value.rs` (`ConfigValue`,
  `Definition`), `de.rs` (custom serde deserializer), `schema.rs` (typed config tables),
  `key.rs`, `path.rs` (`ConfigRelativePath`, `PathAndArgs`), `target.rs` (`[target.*]`),
  `environment.rs`
- Re-exported as `crate::util::GlobalContext`.

## Architecture
Two layers: sources → `ConfigValue` (with `Definition` recording where each value came from),
then `GlobalContext::get::<T>(key)` deserializes on demand; precedence (CLI > env > files, nearer
files over farther) is resolved at retrieval.

## Important constraints
- Env vars must be read via `GlobalContext::get_env` / `get_env_os` (clippy-enforced), so tests
  and `[env]` handling stay consistent.
- Map tables with arbitrary keys have pitfalls with env-var mapping — see "Map key
  recommendations" in `context/mod.rs` before adding one.
- New config keys that are unstable are gated by `-Z` (see [[manifest-and-workspace]]).

## Testing
`tests/testsuite/config*.rs`, `bad_config.rs`, `advanced_env.rs`.
