# os/exec pidfd behavior

Last verified: 2026-09-24

## pidfd_open blocked by seccomp (EPERM) on CI runners
Infra: internal CI runners are Linux 5.15 (corrected 2026-09-24 from an earlier "5.4") with
a seccomp profile that makes `pidfd_open` return `EPERM`. Checked whether os/exec depends
on pidfd and whether a fallback exists.

`checkPidfd()` (src/os/pidfd_linux.go) probes pidfd_open/waitid(P_PIDFD)/pidfd_send_signal/
clone(CLONE_PIDFD) once per process (`sync.OnceValue`); any failure, any errno, permanently
sets `pidfdWorks()` false for that process. `startProcess` (src/os/exec_posix.go) and
`findProcess` (src/os/exec_unix.go) both fall back to `newPIDProcess` (classic Wait4/Kill,
src/os/exec_unix.go `pidWait`/`pidSignal`) when pidfd is unavailable. No error surfaces to
user code; `os.FindProcess` never errors on Unix. `TestFindProcessViaPidfd`
(src/os/pidfd_linux_test.go) already self-skips in this situation.
Caveat: Go can't distinguish "old kernel" from "seccomp-blocked" — both hit the same
permanent per-process fallback, so there's no diagnostic signal that pidfd was blocked
rather than unsupported.

No kernel-version branch exists in this code: checkPidfd() has no `runtime.GOOS`/version
gate for Linux (only GOOS=="android" gets special SIGSYS handling, for old Android's own
seccomp default, unrelated to kernel version). It's a pure runtime capability probe — it
calls the real syscalls and checks the returned error. So the exact minor kernel version
(5.4 vs 5.15) is irrelevant to Go's behavior: 5.15 has all four syscalls pidfd needs
(present since 5.1-5.4 per the file's header comment), so the EPERM the probe sees comes
from the seccomp filter intercepting the call, not from ENOSYS — same permanent fallback,
same lack of diagnostic signal either way.
