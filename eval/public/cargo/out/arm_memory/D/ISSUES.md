# Issues
<!-- Append-only, one entry per bug:
"## ISS-<n> — <title>" heading, then
Symptom: exact error text or observed behavior
Cause: root cause
Fix: commit hash
Test: the test that fails without the fix
Status: open | fixed -->

## ISS-1 — proc-macro test binary cannot find libstd when `--sysroot` is set in rustflags
Symptom: `cargo careful test` on a proc-macro crate: `error while loading shared libraries: libstd-<hash>.so: cannot open shared object file: No such file or directory` (rust-lang/cargo#17351, regression-from-stable-to-nightly)
Cause: #17276 moved sysroot lookup to `GlobalContext`, running a plain `rustc --print=sysroot` without the user's rustflags, so a `--sysroot` in rustflags was ignored for proc-macro runtime lib search paths.
Fix: f3913697b (revert of #17276, PR #17401; a partial fix in #17393 was abandoned as too complex)
Test: none dedicated; the revert restored the earlier `tests/testsuite/cfg.rs` (3ab08e26d)
Status: fixed

## ISS-2 — `cargo clean` reports hardlinked files' size twice
Symptom: `cargo clean --dry-run` summary counted a file and its hardlink as twice the bytes (`2 files, 2.0KiB total` instead of `1.0KiB`)
Cause: size sum in `src/ops/cargo_clean.rs` did not deduplicate by inode
Fix: 5651d3ce4
Test: `tests/testsuite/clean.rs::clean_accounts_for_hardlinks`
Status: fixed
