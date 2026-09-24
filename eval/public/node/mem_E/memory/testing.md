# Testing

## Purpose
How core tests are organised, run, and written.

## Location
- `test/<suite>/` — suite directories; each has a `testcfg.py` and usually a `<suite>.status`.
  Table of suites and whether CI runs them: `test/README.md`.
- `test/common/` — shared helpers (`require('../common')`); API doc in `test/common/README.md`.
- `test/fixtures/` — fixture files.
- `test/cctest/` — C++ gtest unit tests (built into the `cctest` binary).
- `test/wpt/` — Web Platform Tests (vendored in `test/fixtures/wpt/`).
- Runner: `tools/test.py` (Python), using `test/testpy/`.
- Guide: `doc/contributing/writing-tests.md`.

## Running
Requires a built binary (`out/Release/node`, see [[build]]).
```sh
tools/test.py test/parallel/test-stream2-transform.js   # one file
tools/test.py parallel/test-stream-*                    # glob, test/ prefix optional
tools/test.py child-process                             # name substring
make test-only                                          # default suites
make cctest                                             # C++ unit tests
```
A single JS test can also be run directly: `out/Release/node test/parallel/test-x.js`.
`test/common/index.js` reads the `// Flags:` and `// Env:` headers and re-spawns itself with them
if missing (set `NODE_SKIP_FLAG_CHECK=1` to suppress).

### Tmpdir location (`NODE_TEST_DIR`)
`test/common/tmpdir.js` computes `testRoot` from `process.env.NODE_TEST_DIR` (realpath'd) if set,
else defaults to `test/` (`path.resolve(__dirname, '..')`) — note this default is *not* the OS
`/tmp`. The per-worker dir actually used is `<testRoot>/.tmp.<TEST_SERIAL_ID or TEST_THREAD_ID or 0>`.
`tools/test.py` honours `NODE_TEST_DIR` if already exported, otherwise falls back to `--temp-dir`
and exports whichever into `os.environ['NODE_TEST_DIR']` for spawned test processes to inherit
(`tools/test.py` ~line 1797). `--test-root` is unrelated — it only changes where test *files* are
discovered (`tools/test.py` ~line 1670), not where the tmpdir goes.
Practical use: on a runner where the default tmp location is mounted `noexec` (so addon builds or
spawned executables placed there fail with `EACCES`), point `NODE_TEST_DIR` (env var or
`tools/test.py --temp-dir=<path>`) at an exec-mounted directory.

## Writing tests
- `'use strict';` then `require('../common')` **first**, before any other module
  (`require-common-first` lint rule), even if `common` is unused.
- Put a comment describing what is being tested near the top.
- One behaviour per new file: `test/parallel/test-<module>-<what>.js`. Use `test/sequential/`
  only when the test cannot run concurrently (fixed ports, global resources).
- Callbacks that must run are wrapped in `common.mustCall()` / `common.mustSucceed()`;
  never-called ones in `common.mustNotCall()`. Tests must exit cleanly on success.
- Listen on port `0`; use `tmpdir` from `test/common/tmpdir` for files.
- Node flags needed by a test go in a `// Flags: --expose-internals ...` comment near the top
  (within the first 1500 bytes); environment in `// Env: KEY=value`.
- Use `node:assert` strict methods (lint rules `prefer-assert-methods`, `must-call-assert`).

## Status files
`<suite>.status` marks tests per platform section (`[true]`, `[$system==win32]`, ...) as
`PASS,FLAKY` or `SKIP`, each with a link to the tracking issue. `test/known_issues/` holds tests
expected to fail. `$system==aix` and `$system==ibmi` are separate keys (AIX and IBM i are
different CI systems); don't conflate their sections when scanning for one platform. As of
2026-09-24, `test/parallel/parallel.status` has only one `[$system==aix]` entry
(`test-esm-loader-hooks-inspect-wait: PASS, FLAKY`, nodejs/node#54346) and no AIX-specific SKIPs.

## Test parallelism (`-j`)
Both `tools/test.py` and the `Makefile` pick worker count from CPU count only, never from
available RAM: `test.py` defaults `-j` to `int(os.environ['JOBS'])` if that env var is set, else
`multiprocessing.cpu_count()` (`ProcessOptions`, `tools/test.py` ~line 1500); the `Makefile` only
sets `-j`/`PARALLEL_ARGS` when the caller exports `JOBS` (~line 29), otherwise leaves it to
`test.py`'s default. Per the Build WG (2026-09-24), the Jenkins AIX test machines have 16 GB RAM
each (not 4 GB as earlier assumed) — moot for parallelism sizing either way, since no code path
here scales jobs by memory.

## Benchmarking
`benchmark/` holds performance benchmarks (separate from `test/`), run with a built binary via
`benchmark/run.js` or a benchmark file directly, e.g. `out/Release/node benchmark/misc/startup-core.js`.
Guide: `doc/contributing/writing-and-running-benchmarks.md`. Startup cost specifically is covered by
`benchmark/misc/startup-core.js` (spawns the binary against fixture scripts in `process`/`worker`
mode, 30 runs + 3 warmup by default) and `benchmark/misc/startup-cli-version.js` (times `--version`
for vendored CLIs: npm, npx, corepack, eslint).

## Important Constraints
- Project policy (`doc/contributing/ai-guidelines.md`): existing tests must not be removed or
  modified without human verification; new tests should test intended behaviour, not merely
  mirror what the implementation happens to do.
