# External systems
<!-- Only what the code cannot tell you: provider quirks, deferred constraints, what the deploy runs,
which credentials reach what, environment traps. Move a topic to its own file once it passes ~40 lines. -->

## Jenkins AIX test machines
AIX 7.2 TL5, 16 GB RAM each (corrected by Build WG 2026-09-24; earlier note said 4 GB).
As of commit 342bf6d669, test/parallel/parallel.status `[$system==aix]` block lists only
1 entry: test-esm-loader-hooks-inspect-wait (PASS, FLAKY, nodejs/node#54346). No AIX
tests are marked SKIP. If AIX CI shows new flakiness/timeouts, suspect the 16 GB ceiling
before assuming it's already flagged here.

Neither tools/test.py nor the Makefile picks test parallelism based on memory: Makefile's
`-j`/`JOBS` is passed through as-is (e.g. jstest rule, line ~324), and tools/test.py falls
back to `multiprocessing.cpu_count()` when `-j`/`JOBS` isn't set (tools/test.py:1500-1504).
The only memory-related knob is `TestCase.max_virtual_memory` (tools/test.py:568), a
per-test RLIMIT_AS cap on Linux, unrelated to job count. So the 4 GB->16 GB correction
doesn't change any existing parallelism defaults — it was never read for that purpose.

Last verified: 2026-09-24

## Internal build farm: /tmp is noexec
On our internal build farm, /tmp is mounted noexec, so any test that writes an
executable or native addon into the test tmpdir and runs it fails with EACCES.
Workaround: point NODE_TEST_DIR at an exec-mounted directory. Confirmed in
test/common/tmpdir.js (line ~35): `testRoot` uses
`fs.realpathSync(process.env.NODE_TEST_DIR)` when that env var is set,
otherwise falls back to `path.resolve(__dirname, '..')` (test/). The per-test
tmpdir (`.tmp.<id>`, used by refresh()/resolve()) is created under testRoot,
so NODE_TEST_DIR does redirect where test binaries/addons land and execute.

Last verified: 2026-09-24
