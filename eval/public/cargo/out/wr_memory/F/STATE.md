# State
<!-- Now only. Overwritten every session. Finished work leaves. Cap 60 lines. -->

Goal: Cargo, the Rust package manager (README.md)

## Deployed
Ships with Rust releases, not deployed separately (README.md "Releases")

## Broken
- none known

## Open threads
- builtin dependencies (unstable `cargo-features = ["builtin-dependencies"]`, src/workspace/features.rs): manifest validation landed in e2f915c85 (#17499), regression tests in 694054f34 (#17500)

## Next 3
1. 
2. 
3. 

## Last session
<!-- Rewritten at every close, ~10 lines. Where the last session stopped, so the next one resumes cleanly. -->
Branch: eval
Uncommitted: none
Stopped at: corrected the Artifactory mirror rate limit in memory/external.md from 60 to
120 req/min per IP (infra team correction, 2026-09-24). Checked src/util/network/retry.rs and
the rest of the codebase — nothing derives its backoff schedule from that number, so no code
change was needed.
Tried, failed: 
Resume with: 

Last updated: 2026-09-24
