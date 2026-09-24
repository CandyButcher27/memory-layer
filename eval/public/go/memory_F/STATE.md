# State
<!-- Now only. Overwritten every session. Finished work leaves. Cap 60 lines. -->

Goal: The Go programming language: compiler, toolchain, runtime and standard library (README.md).

## Deployed
Not deployed; a source tree. HEAD 41fd3e5b1b on master (2026-09-24).

## Broken
- none known locally

## Open threads
- CL 834945 (LUCI builder detection in cmd/dist) reverted in ab269a42a4; blocked on TestAllDependencies not writing to GOROOT. See ISS-1.

## Next 3
1. 
2. 
3. 

## Last session
<!-- Rewritten at every close, ~10 lines. Where the last session stopped, so the next one resumes cleanly. -->
Branch: master
Uncommitted: none (memory/external.md + CLAUDE.md index committed)
Stopped at: infra corrected CI runner kernel from Linux 5.4 to 5.15 (seccomp pidfd_open block unchanged); confirmed src/os/pidfd_linux.go's checkPidfd() has no kernel-version branch for Linux (only GOOS=="android" is special-cased) — it's a pure runtime syscall probe, so 5.4 vs 5.15 doesn't change the EPERM/fallback behavior already recorded in memory/os-exec.md. No code changed (investigation only). Updated memory/os-exec.md.
Tried, failed: (none this session)
Resume with: 

Last updated: 2026-09-24
