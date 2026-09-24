# Testing

## Location
- `tests/testsuite/` — one integration test binary (`main.rs` declares ~200 modules); per-feature
  modules (e.g. `builtin_dep.rs`) and per-command UI dirs (`cargo_<cmd>/`)
- `tests/build-std/` — real `-Zbuild-std` tests
- `crates/cargo-test-support` — `project()`, `registry`, `git`, `str![]` / `file![]` snapshots,
  `paths` (sandboxed `CARGO_HOME`/root); `crates/cargo-test-macro` — `#[cargo_test]`
- Contributor docs: `doc/contrib/src/tests/{writing,running}.md`

## Conventions
- Always `#[cargo_test]`, never `#[test]`, in the testsuite; it isolates HOME/CARGO_HOME.
- Expected output uses snapbox `str![[r#"..."#]]` with `[ROOT]`, `[..]`, `[ERROR]` redactions.
  Update with `SNAPSHOTS=overwrite cargo test --test testsuite -- <filter>` and review the diff.
- Nightly-only behavior: `#[cargo_test(nightly, reason = "...")]` when it needs a nightly rustc;
  for Cargo's own unstable features use `.masquerade_as_nightly_cargo(&["feat"])` instead.
- Test commits precede fix commits and record current (possibly buggy) behavior.

## Gated categories (env vars)
- Cross tests need a second target installed; skip with `CFG_DISABLE_CROSS_TESTS=1`.
- `CARGO_RUN_BUILD_STD_TESTS=1` (nightly + `rust-src`), `CARGO_PUBLIC_NETWORK_TESTS=1`,
  `CARGO_CONTAINER_TESTS=1` (Docker).

## CI (`.github/workflows/main.yml`)
fmt, clippy, `lint-docs --check`, version-bump check, `cargo test -p cargo` on stable/beta/nightly
across OSes, other workspace crates, schemas, resolver-tests, build-std, man-page validation.
