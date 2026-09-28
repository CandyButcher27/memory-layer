# External systems
<!-- Only what the code cannot tell you: provider quirks, deferred constraints, what the deploy runs,
which credentials reach what, environment traps. Move a topic to its own file once it passes ~40 lines. -->

## CI Artifactory mirror rate limit (no Retry-After on 429)
CI points cargo at an internal Artifactory mirror of crates.io that rate-limits each IP to 120 req/min and never sends a `Retry-After` header on its 429s (per infra team, corrected 2026-09-28).
Without that header, `Retry::parse_retry_after` (src/util/network/retry.rs) returns `None`, so cargo falls back to its default backoff in `next_sleep_ms`: ~0.5-1.5s on the first retry, then `(retries-1)*3s + 0.5s` up to a 10s cap, for `net.retry` (default 3) attempts total. That schedule isn't paced to a 120/min budget, so a burst of parallel requests can keep re-hitting the limit instead of backing off enough to clear it.

## Windows build agents: Defender locks freshly-linked test .exe (~2s)
Corporate Defender policy on our Windows build agents locks every newly-written `.exe` under `target/` for about 2s after it's written (per IT, 2026-09-28), so `cargo test` can fail spawning a just-linked test binary with `Access is denied. (os error 5)`.

Cargo has no delay or retry between linking and spawning a test binary: `run_unit_tests` (src/ops/cargo_test.rs) calls `cmd.exec()` immediately after `compile_tests` finishes linking each unit. `ProcessBuilder::exec` → `_status` → `Command::spawn` (crates/cargo-util/src/process_builder.rs) only retries on "command line too big" (`should_retry_with_argfile`, keyed on `E2BIG`/`ERROR_FILENAME_EXCED_RANGE`), not on access-denied or other spawn errors. A spawn failure surfaces as `ProcessError::could_not_execute` and fails the run (or is recorded per-unit under `--no-fail-fast`).

Last verified: 2026-09-28
