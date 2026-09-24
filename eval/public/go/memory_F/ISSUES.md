# Issues
<!-- Append-only, one entry per bug:
"## ISS-<n> — <title>" heading, then
Symptom: exact error text or observed behavior
Cause: root cause
Fix: commit hash
Test: the test that fails without the fix
Status: open | fixed -->

## ISS-1 — TestAllDependencies fails on longtest builders after LUCI builder-detection change
Symptom: `TestAllDependencies` (src/cmd/internal/moddeps/moddeps_test.go) breaks on longtest builders once CL 834945 (commit 936cd9c3e8, "cmd/dist: update Linux builder detection for LUCI") is in.
Cause: the test writes to GOROOT, which is not writable on those builders (revert message of ab269a42a4; same class as 115f2c3673).
Fix: ab269a42a4 reverts 936cd9c3e8. Not relanded as of 41fd3e5b1b; relanding needs TestAllDependencies changed to not write to GOROOT first.
Test: TestAllDependencies on a longtest builder
Status: open
