# Issues
<!-- Append-only, one entry per bug:
"## ISS-<n> — <title>" heading, then
Symptom: exact error text or observed behavior
Cause: root cause
Fix: commit hash
Test: the test that fails without the fix
Status: open | fixed -->

## ISS-1 — `cargo run` error line overwritten when the program's last output ends in `\r`
Symptom: a binary that prints `hewwo\r` then exits 1 makes `cargo run`'s "process didn't exit successfully" error overwrite that line (seen on Windows), issue #17343
Cause: the error was printed without first moving to a new line
Fix: e58ed5577 (#17373) — `writeln!(gctx.shell().err())` before the error
Test: `cargo test -p cargo --test testsuite -- run::exit_code run::exit_code_verbose`
Status: fixed

## ISS-2 — `cargo clean` summary double-counts size of uplifted hardlinks
Symptom: `cargo clean --dry-run` printed `Summary 2 files, 2.0KiB total` for one 1 KiB file plus its hardlink
Cause: each hardlink's size was added separately
Fix: 5651d3ce4 (merged in cc7400190, #17485)
Test: `tests/testsuite/clean.rs` `clean_accounts_for_hardlinks` (expects `1.0KiB total`)
Status: fixed
