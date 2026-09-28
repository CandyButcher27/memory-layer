# State
<!-- Now only. Overwritten every session. Finished work leaves. Cap 60 lines. -->

Goal: Cargo, Rust's package manager and build tool (README.md)

## Deployed
Not deployed from here; ships with Rust toolchains. Checkout is a detached HEAD at 694054f34.

## Broken
- none known

## Open threads
- Recent upstream activity is builtin-dependencies manifest validation (e2f915c85 #17499, 694054f34 #17500)
- `rust-version` discrepancy in Cargo.toml: `[workspace.package]` sets 1.95 (line 14), but the `cargo`
  package itself and most member crates (cargo-util, cargo-util-terminal, crates-io,
  cargo-util-schemas, cargo-test-macro, cargo-test-support, and the wincred/macos-keychain/libsecret
  credential crates) override it to 1.98 (line 151 and others); a smaller set (build-rs, cargo-platform,
  home, rustfix, cargo-credential, cargo-credential-1password) inherits the 1.95 default. Needs Priya
  Raman's sign-off before either value changes — see memory/external.md.
- Internal fork must be rebased onto upstream before 2026-10-15 (release branch cut date).
- New config key `net.retry-max-delay` (seconds, default 10) in progress: step 1 done (schema field);
  steps 2 (wire into src/util/network/retry.rs) and 3 (docs + unit test) still open.
- Reported: `cargo clean -p foo` allegedly leaves stale `.rmeta` behind when `foo` is depended on via
  rename (`bar = { package = "foo" }`). Not yet reproduced (no cargo/rustc in this sandbox to test).
  Ruled out today: release-vs-debug profile-dir logic (repros in debug too), file locking (repros with
  a single cargo process). Static read of src/ops/cargo_clean.rs, compilation_files.rs::pkg_dir/
  compute_metadata, and fingerprint/mod.rs::DepFingerprint found the rename only feeds the *dependent's*
  fingerprint hash (via extern_crate_name), not `foo`'s own crate_name/pkg_dir/hash — so no mismatch
  found by inspection. User's next suspect: the name match in cargo_clean.rs::clean_specs itself.

## Next 3
1. Wire `retry_max_delay` into src/util/network/retry.rs (`Retry::new`, `next_sleep_ms`, Retry-After
   cap), replacing `MAX_RETRY_SLEEP_MS`; read it via `net_config()`, not a raw env var; leave jitter as-is.
2. Document `net.retry-max-delay` in the config reference.
3. Add a unit test for the new key (default-unset case must still be 10s).

## Last session (2026-09-28)
Branch: detached HEAD at 694054f34
Uncommitted: CLAUDE.md, ISSUES.md, STATE.md, decisions.md, memory/ (memory layer files, all untracked);
  src/context/schema.rs (added `retry_max_delay: Option<u64>` to `CargoNetConfig`, step 1 of
  net.retry-max-delay task, still not wired in — untouched this session)
Stopped at: investigated the `cargo clean -p` renamed-dependency `.rmeta` report (see Open threads).
  No code change made; no repro yet, only code-reading. Next step user wants is a failing testsuite
  case, not a fix.
Resume with: write a failing test in tests/testsuite/clean.rs — path dependency renamed via
  `bar = { package = "foo", path = ... }`, build, `cargo clean -p foo`, assert whether `.rmeta`
  survives — to confirm/deny the clean_specs name-matching theory before touching cargo_clean.rs.

Last updated: 2026-09-28
