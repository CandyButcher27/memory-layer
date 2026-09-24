# External systems
<!-- Only what the code cannot tell you: provider quirks, deferred constraints, what the deploy runs,
which credentials reach what, environment traps. Move a topic to its own file once it passes ~40 lines. -->

Last verified: 2026-09-23 (runner timeout corrected to 60 min; ci/ re-checked for own timeout settings)

## Patches go to the mailing list, not GitHub pull requests
git/git on GitHub does not take pull requests. Code, review and bug reports go to git@vger.kernel.org;
GitGitGadget (https://gitgitgadget.github.io/) turns a GitHub PR into mailing-list patches. For a
single-commit PR, leave the description empty: the commit message is the description.
Source: .github/PULL_REQUEST_TEMPLATE.md, README.md, Documentation/SubmittingPatches.
Security issues go privately to git-security@googlegroups.com (README.md).

## Self-hosted runners: Alpine 3.20 musl, 60-minute hard kill
Our fork's self-hosted CI runners run Alpine Linux 3.20 (musl libc), each job hard-killed at 60
minutes (corrected 2026-09-23 by infra team; previously recorded as 45). Audited `ci/` on
2026-09-23: no glibc- or distro-specific assumptions found. musl/Alpine is already a first-class
target — `ci/install-dependencies.sh` has an `alpine-*)` branch (apk, installs `bash` since Alpine
has no bash by default), `ci/lib.sh` sets `-Dtest_utf8_locale=C.UTF-8` for `linux-musl-meson`
(musl locale quirk), and `linux-musl-meson` / `fedora-breaking-changes-musl` jobs exist in
`ci/run-build-and-tests.sh`. Trap: `ci/lib.sh` picks the `alpine-*` branch only when `distro`
(derived from `CI_JOB_IMAGE`/`jobname`) matches `alpine:*` or `linux-musl-meson` — a self-hosted
runner must set that env var/job name correctly or `lib.sh` exits with "Could not identify OS
image" instead of taking the musl path. Re-checked 2026-09-23: no `timeout-minutes` in
`.github/workflows/*.yml` and only `timeout: 2h`/`timeout: 6h` in `.gitlab-ci.yml` (GitLab SaaS
runners, tag `saas-*`, unrelated to our self-hosted fleet); no script in `ci/` sets its own
timeout. Any timeout enforcement for the self-hosted fleet is at the runner/infra level, outside
this repo.

## Corporate HTTP proxy strips Git-Protocol header (silent v0 fallback)
Our internal mirror is only reachable through a corporate HTTP proxy that strips the
`Git-Protocol` request header. The client sends it from `remote-curl.c` (`get_protocol_http_header()`,
`remote-curl.c:397-408`), attached to both the `info/refs` discovery request
(`remote-curl.c:503-505`) and the stateful RPC request (`remote-curl.c:1129-1132`). With the
header gone, `http-backend.c:822-824` never sets `GIT_PROTOCOL` server-side, so every HTTPS fetch
from the mirror silently negotiates v1 instead of v2 — no error, no warning. Lost: on-demand
`ls-refs` filtering (full ref advertisement returned on every request instead), `wanted-ref`/
`shallow-since`/`packfile-uris`/`wait-for-done` fetch-command args, `server-option`. No fix
attempted (network changes out of scope); if this needs fixing, it's a proxy allowlist change, not
a Git code change.
Source: traced 2026-09-23 at eab8f481f6; Documentation/gitprotocol-v2.adoc "HTTP Transport".

## `make` fails when cargo/rustc is not installed
Since 2.55 Rust is on by default in both build systems (Makefile `ifndef NO_RUST`, meson `rust`
option default `enabled`). Without a Rust toolchain, build with `make NO_RUST=YesPlease` or
`meson configure -Drust=disabled`. The option goes away in Git 3.0 (see DEC-1 in decisions.md).
Source: Makefile "Optional Rust support" comment; meson_options.txt; Documentation/BreakingChanges.adoc.
