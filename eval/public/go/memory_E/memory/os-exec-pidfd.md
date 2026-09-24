---
name: os-exec-pidfd
description: How os/os-exec process handling uses Linux pidfd and falls back when pidfd_open is unavailable (e.g. blocked by seccomp)
metadata:
  type: project
---

`os/exec` never touches pidfd itself — it starts processes through `os.StartProcess`/`os.Process`,
so all pidfd behavior lives in the `os` and `syscall` packages on `linux`:

- `src/os/pidfd_linux.go` — `ensurePidfd`, `getPidfd`, `pidfdFind`, `Process.pidfdWait`,
  `Process.pidfdSendSignal`, and the capability probe.
- `src/internal/syscall/unix/pidfd_linux.go` — raw `pidfd_open`/`pidfd_send_signal` syscall wrappers.
- `src/syscall/exec_linux.go` — sets `CLONE_PIDFD` on `clone()` when `SysProcAttr.PidFD != nil`,
  and `checkClonePidfd` (linknamed into `os`) which verifies `clone(CLONE_PIDFD)` actually returns
  a pidfd.
- `src/os/pidfd_other.go` — non-Linux unix/js/wasip1/windows build stub: pidfd is unconditionally
  "not available" there (Windows has its own handle path in `exec_windows.go`, unrelated to Linux
  pidfd).

**Capability probe, and why it's safe under seccomp:** `checkPidfd()` (`pidfd_linux.go`) runs at
most once per process, cached via `sync.OnceValue` as `checkPidfdOnce`/`pidfdWorks()`. It opens a
pidfd on the calling process, calls `waitid(P_PIDFD, ...)` (expects `ECHILD`), calls
`pidfd_send_signal(fd, 0)`, and calls `checkClonePidfd()` (an actual `clone(CLONE_PIDFD)` +
reap). **Any failure at any step — `ENOSYS` on old kernels, `EPERM` from a seccomp filter blocking
`pidfd_open`, or anything else — is treated the same way**: the error is cached and `pidfdWorks()`
returns `false` for the rest of the process's life. There is no per-call retry and no distinction
between "syscall missing" and "syscall blocked".

**Fallback path, fully wired:** every pidfd entry point checks `pidfdWorks()` first and no-ops if
it's false:
- `ensurePidfd` returns the original `SysProcAttr` unchanged (so `syscall.forkAndExecInChild`
  never sets `CLONE_PIDFD`, i.e. `pidfd_open` and `clone(CLONE_PIDFD)` are each attempted exactly
  once total, during the first `checkPidfd()` call, never again).
- `getPidfd` returns `(0, false)`, so `os/exec_posix.go:startProcess` falls back to
  `newPIDProcess(pid)`.
- `pidfdFind` returns `ENOSYS`, so `os/exec_unix.go:findProcess` falls back to
  `newPIDProcess(pid)` (only `ErrProcessDone`/`ESRCH` short-circuits to a done-process; every other
  error, including `ENOSYS`, falls back).
- `Process.wait`/`Process.signal` branch on `p.handle != nil`; with no handle they use
  `pidWait`/`pidSignal` (plain `Wait4`/`Kill` syscalls) unconditionally.

Net effect: on a runner where seccomp returns `EPERM` for `pidfd_open`, the very first
`checkPidfd()` call fails fast, gets cached, and every subsequent process start/wait/signal in
that process silently uses the legacy PID-based path — no crash, no hang, no explicit opt-in
needed. This is independent of kernel version: `checkPidfd()` treats `ENOSYS` (syscall missing,
old kernel) and `EPERM` (syscall present but blocked by seccomp) identically, so a newer kernel
does not change the outcome as long as the seccomp rule blocking `pidfd_open` stays in place. (CI
runners are on Linux 5.15 as of 2026-09-24, which is new enough for every pidfd-related syscall
`checkPidfd()` uses — see the version table in `pidfd_linux.go`'s file header — but the CI seccomp
profile still blocks `pidfd_open`, so the fallback path is what actually runs there.) This is
exercised directly by
`src/os/pidfd_linux_test.go` (`TestProcessWithHandleLinux` runs the assertions for both the
pidfd-available and pidfd-unavailable branches in the same test, gated on `os.CheckPidfdOnce()`)
and by `src/os/exec_unix_test.go` for the PID-only path.

Two things that are *not* covered by this fallback and would need real pidfd support: explicitly
setting `syscall.SysProcAttr.PidFD` and then reading it back (the caller gets a `-1`, per the
`PidFD` field doc in `exec_linux.go`), and `Process.WithHandle`, which returns an error if pidfd
isn't available rather than falling back to anything.

See also [[runtime]] for the linknamed `ignoreSIGSYS`/`restoreSIGSYS` runtime hooks used only on
`GOOS=android` (unrelated to generic seccomp EPERM handling — Android blocks pidfd syscalls with
`SIGSYS` instead of returning `EPERM`, on API levels below 12).
