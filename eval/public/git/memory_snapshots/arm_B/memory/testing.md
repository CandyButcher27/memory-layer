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
