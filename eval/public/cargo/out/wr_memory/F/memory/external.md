# External systems
<!-- Only what the code cannot tell you: provider quirks, deferred constraints, what the deploy runs,
which credentials reach what, environment traps. Move a topic to its own file once it passes ~40 lines. -->

## CI registry mirror (internal Artifactory) has no Retry-After on 429
CI points cargo at an internal Artifactory mirror of crates.io. It rate-limits each IP to 120 req/min
and its 429 responses never include a `Retry-After` header (confirmed with infra team, 2026-09-24;
corrected from an earlier reported 60 req/min, also 2026-09-24). Without that header,
`Retry::parse_retry_after` (src/util/network/retry.rs) returns `None` and cargo falls back to its
generic exponential-backoff schedule in `Retry::next_sleep_ms`: ~0.5-1.5s, then 3.5s, then 6.5s, capped
at `MAX_RETRY_SLEEP_S` = 10s, for `net.retry` (default 3) retries. That schedule is not derived from
the mirror's req/min limit, so bursts of concurrent requests can keep hitting 429 and exhaust retries.
If this shows up as a CI failure, look for `HttpNotSuccessful { code: 429, .. }` in the error, not a
hang — cargo gives up after 4 total attempts (~10.5s max).

Last verified: 2026-09-24

## `Access is denied. (os error 5)` running a freshly built test binary on Windows CI agents
IT confirmed (2026-09-24): corporate Defender policy on our Windows build agents locks every
newly written `.exe` under `target/` for ~2s after link. `cargo test` has no delay or retry to
absorb this: `run_unit_tests` (src/ops/cargo_test.rs) calls `cmd_builds` then immediately
`cmd.exec()` on the same iteration the build finished, and `ProcessBuilder::exec` ->
`status()` (crates/cargo-util/src/process_builder.rs) does a single `Command::spawn()` with no
retry on spawn failure. So the first test binary to run right after `cargo test` finishes
linking can lose the race with Defender's scan and fail to spawn with this exact error. It is
an environment race, not a cargo bug; cargo does not read `Retry-After`-style hints here because
there's no process to negotiate with, just a locked file handle.

Last verified: 2026-09-24
