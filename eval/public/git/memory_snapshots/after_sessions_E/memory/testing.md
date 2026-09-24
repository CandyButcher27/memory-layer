# Test suite

## Purpose
Shell integration tests (TAP) plus clar-based C unit tests, with lint gates that CI enforces.

## Location
- `t/tNNNN-*.sh` (~1000 scripts), `t/test-lib.sh`, `t/test-lib-functions.sh`, `t/lib-*.sh`
- `t/helper/` — `test-tool` subcommands exposing internals to shell tests
- `t/unit-tests/u-*.c` (clar suites), `t/unit-tests/clar/`, `lib-oid`, `lib-reftable`
- `t/chainlint.pl`, `t/greplint.pl`, `t/check-non-portable-shell.pl`
- `t/README` — authoritative guide; `ci/` — CI job definitions (`ci/lib.sh`)

## Architecture
- Scripts use `test_expect_success '<title>' '<body>'` and end with `test_done`. Each runs in a
  fresh trash directory with fixed author/committer identity and dates.
- `t/test-lib.sh` sets `GIT_DEFAULT_HASH` from `GIT_TEST_DEFAULT_HASH` (else the binary's
  built-in default) and `GIT_DEFAULT_REF_FORMAT` from `GIT_TEST_DEFAULT_REF_FORMAT` (else
  `files`). Many other `GIT_TEST_*` knobs are documented in `t/README`.
- Unit suites are listed in `Makefile` (`CLAR_TEST_SUITES +=`) and `t/meson.build`
  (`clar_test_suites`); integration scripts in `t/meson.build` (`integration_tests`).

## Commands
- One script: `cd t && sh ./tNNNN-name.sh -v -i` (`-d` keeps trash dir, `-x` traces).
- All: `make -C t` or `make DEFAULT_TEST_TARGET=prove GIT_PROVE_OPTS=-j8 test`.
- Unit: `make unit-tests`. Lint: `make -C t test-lint`; meson list sync: `make -C t check-meson`.

## Important Constraints
- `&&`-chain every command in a test body; `chainlint` rejects breaks.
- Shell must be portable POSIX (checked by `check-non-portable-shell.pl`).
- New scripts/suites must be added to `t/meson.build` or `check-meson` fails.
- CI runs leak (`SANITIZE=leak`) and ASan/UBSan jobs; new code must not leak.

## CI portability (musl / Alpine)
- `ci/` scripts already handle Alpine/musl as a first-class case, not an afterthought: `distro`
  is matched against `alpine-*` in `ci/install-dependencies.sh` (installs via `apk`, adds `bash`
  since it's not the default shell, and stubs `sudo` to a no-op when running as root because
  Alpine has no `sudo` by default) and against `linux-musl-meson` in `ci/lib.sh` /
  `ci/run-build-and-tests.sh` (sets `-Dtest_utf8_locale=C.UTF-8`, disables Rust via
  `-Drust=disabled`). Checked 2026-09-23: no script calls glibc-only tools (`ldd`,
  `/etc/os-release`, `dpkg`, `__GLIBC__`) outside distro-guarded branches.
- `ci/lib.sh` sets `GIT_TEST_LONG=true` for pull-request events and pushes to
  `master`/`main`/`next`/`maint`, enabling the expensive test subset. Why: gives PRs maximum
  coverage before merge. How to apply: on a runner with a hard wall-clock kill (self-hosted
  runners here cap jobs at 60 minutes, per infra team, corrected 2026-09-23 from an earlier
  45-minute figure), this is the more likely cause of a killed job than any distro/libc mismatch —
  check this env var first when a self-hosted job times out. Confirmed 2026-09-23: nothing in
  `ci/` or `.github/workflows/main.yml` sets its own `timeout-minutes` or wall-clock timeout, so
  the 60-minute runner cap is the only limit in play — no in-repo setting competes with or
  shortens it.
