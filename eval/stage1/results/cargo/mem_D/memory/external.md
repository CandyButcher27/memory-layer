# External systems and traps
<!-- Only what the code cannot tell you: provider quirks, deferred constraints, what the deploy runs,
which credentials reach what, environment traps. Move a topic to its own file once it passes ~40 lines. -->

Last verified: 2026-08-27

## Moving sysroot lookup into GlobalContext regressed and was reverted
PR #17276 (fee70b3bf) moved the sysroot lookup to `GlobalContext`; it caused issue #17351 and was
reverted in f3913697b (#17401), marked for beta backport. A fix-forward attempt (#17393) was dropped as
"more complex than we thought". Read #17351 before trying this refactor again.

## CI cannot reach crates.io directly
Security team blocked direct crates.io access from CI in July 2026; all registry traffic goes through
an internal mirror via `[source]` replace-with in `.cargo/config.toml`.

## Internal mirror prunes yanked crates every Sunday night, breaking Monday builds
Unlike crates.io (which never deletes yanked crate files, only hides them from new resolution), the
internal mirror deletes yanked versions outright on its weekly prune. A `Cargo.lock` pinned to a version
yanked before that Sunday's prune fails to download on Monday even though cargo itself has no problem
reusing an already-locked yanked version. Has recurred twice as of 2026-09-28.

## `cargo test` CI runtime is dominated by the `testsuite` target
Full `cargo test` on CI has a 23 min median over the last 20 runs (as of 2026-09-20). Most of that is
one integration test binary, `tests/testsuite/main.rs` (~200 `mod` per feature/subcommand, using
`cargo-test-support`), whose `#[cargo_test]` fns mostly shell out to real `cargo` subprocesses.

## CI runners use sccache with a 50 GB local cache limit per runner
Stated 2026-09-28; not a known problem yet, just the current cap.

## Resolver changes need a second reviewer from the platform team
Applies to anything touching `src/resolver` (stated 2026-09-28).

## MSRV bumps need Priya Raman's sign-off
She owns changes to `rust-version` workspace-wide; get her sign-off before bumping it (stated
2026-09-28). See STATE.md for the current `rust-version` discrepancy between the workspace default and
the `cargo` package/most crates, flagged to her and not yet resolved.
