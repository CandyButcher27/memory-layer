# State
<!-- Now only. Overwritten every session. Finished work leaves. Cap 60 lines. -->

Goal: Cargo, the Rust package manager (README.md)

## Deployed
Not deployed; ships with the Rust toolchain. Checkout is detached HEAD at 694054f34 (2026-09-23), branch `master` upstream.

## Broken
- none known

## Open threads
- Unstable `builtin-dependencies` feature: manifest syntax and validation landed in #17497, #17498, #17499, #17500 (git log --grep builtin-deps)
- Unstable trim-paths: breaking changes in progress (`fix(trim-paths)!` commits, e.g. 3c0b53475, 1a27c0c81)

## Next 3
1. none recorded
2.
3.

## Last session
Branch: detached HEAD 694054f34
Uncommitted: nothing (memory layer files committed)
Stopped at: traced where `cargo test` spawns test binaries (src/ops/cargo_test.rs `run_unit_tests` → `cmd_builds` → `ProcessBuilder::exec`); confirmed no delay/retry between linking and spawn, recorded as memory/external.md Windows Defender lock entry; no code changed
Tried, failed: nothing
Resume with: nothing pending

Last updated: 2026-09-28
