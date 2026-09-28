# Build performance

## Release build time on CI runner (8 vCPU)
`cargo build --release` on the CI runner (8 vCPU): 6m41s, median of 5 runs, measured 2026-09-22.
No `[profile.release]` override exists anywhere in the workspace root `Cargo.toml` (only test-fixture
`[profile.release.package.*]` blocks under `tests/testsuite/`, which aren't real config) and
`.cargo/config.toml` sets no `[build]`/jobs limit, so this is Cargo's built-in release defaults
(`opt-level = 3`, `codegen-units = 16`, `lto = false`) building ~130 workspace crates — not a
profile misconfiguration.

Last verified: 2026-09-22
