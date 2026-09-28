# Issues
<!-- Append-only, one entry per bug:
"## ISS-<n> — <title>" heading, then
Symptom: exact error text or observed behavior
Cause: root cause
Fix: commit hash
Test: the test that fails without the fix
Status: open | fixed -->

## ISS-1 — write_atomic through a relative symlink writes to the wrong file
Symptom: `cargo_util::paths::write_atomic` on a symlink with a relative target fails, or overwrites an unrelated file relative to the process working directory (rust-lang/cargo#17361)
Cause: `fs::read_link` returns the target as stored; it was used without joining onto the symlink's parent directory
Fix: 70ce89528 (merged in 8d4bb1e0c, #17362)
Test: `write_atomic_relative_symlink` in crates/cargo-util/src/paths.rs (added 991371edc)
Status: fixed

## ISS-2 — `cargo clean` summary double-counts hardlinked files
Symptom: `cargo clean --dry-run` reports `Summary 2 files, 2.0KiB total` when the two files are hardlinks of one 1 KiB file
Cause: size was summed per path, not per inode
Fix: 5651d3ce4
Test: `clean_accounts_for_hardlinks` in tests/testsuite/clean.rs
Status: fixed

## ISS-3 — moving sysroot lookup into GlobalContext caused a regression
Symptom: regression reported as rust-lang/cargo#17351 (exact text not in the repo; read the issue)
Cause: #17276 moved sysroot lookup to `GlobalContext`; a fix attempt (#17393) found it "more complex than we thought"
Fix: reverted in f3913697b (#17401, marked for beta backport); revert conflicted in src/compiler/trim_paths.rs
Test: tests/testsuite/cfg.rs changes in 3ab08e26d
Status: fixed by revert; do not re-land #17276 as-is
