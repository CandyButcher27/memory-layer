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

## Retry/backoff on network errors (`src/util/network/retry.rs`)
- `maybe_spurious` treats HTTP 429 the same as 5xx: always retryable, regardless of headers.
  Retry count is `net.retry` config (default `MAX_RETRY_DEFAULT = 3`, i.e. 4 attempts total).
- `Retry::parse_retry_after` looks for a `Retry-After` header only on 429/503 responses, and
  only when present does it honor the server-requested delay (seconds, or an RFC 2822 HTTP
  date) — capped at `MAX_RETRY_SLEEP_S = 10` seconds via `.min(MAX_RETRY_SLEEP_MS)`.
- **If there is no `Retry-After` header (or it's absent/unparseable), the 429/503 falls back to
  the same schedule as any other spurious error** (`next_sleep_ms`): ~0.5-1.5s jittered after
  the first failure, then `(retries-1)*3 + 0.5` seconds capped at 10s. There is no per-429
  minimum backoff distinct from a 500 — cargo does not slow down more aggressively just because
  the server said 429 vs 503, unless that server also sends `Retry-After`.
- Practical implication: a rate limiter that returns 429 without `Retry-After` gets retried on
  the generic backoff schedule (sub-2s after the first hit), which can still exceed a strict
  per-minute rate limit under retry storms from many concurrent cargo/CI invocations, since
  there's no cross-process coordination of the retry schedule.

## Testing
`tests/testsuite/registry*.rs`, `git*.rs`, `alt_registry.rs`, `vendor.rs`, `source_replacement.rs`;
fixtures via `cargo_test_support::registry` and `::git`. Git/SSH container tests need
`CARGO_CONTAINER_TESTS=1`.
