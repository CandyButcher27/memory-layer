<!-- Only what the code cannot tell you: measured build numbers, why a build choice is non-obvious. -->

## `cargo build --release` full-workspace baseline: 6m41s median on CI (8 vCPU)
Median of 5 runs, CI runner (8 vCPU), 2026-09-22: 6m41s. Root `Cargo.toml` has no `[profile.release]`
override (checked: no `[profile.*]` table in the workspace manifest), so the build uses Cargo's stock
release defaults (opt-level=3, lto=false, codegen-units=16, debug=false). Nothing in the profile config
explains the time; it reflects dependency count/compile cost (git2, curl, openssl-src, rusqlite bundled,
gix, etc.). If this build gets meaningfully slower or faster, re-measure and update this line rather than
assuming a profile regression.

Last verified: 2026-09-22
