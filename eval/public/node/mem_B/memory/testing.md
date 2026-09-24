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
expected to fail.

## Important Constraints
- Project policy (`doc/contributing/ai-guidelines.md`): existing tests must not be removed or
  modified without human verification; new tests should test intended behaviour, not merely
  mirror what the implementation happens to do.
