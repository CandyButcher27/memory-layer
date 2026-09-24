# External systems
<!-- Only what the code cannot tell you: provider quirks, deferred constraints, what the deploy runs,
which credentials reach what, environment traps. Move a topic to its own file once it passes ~40 lines. -->

Last verified: 2026-09-24

## GitHub pull request is not merged on GitHub
The canonical repo is Gerrit (https://go.googlesource.com/go, reviews at go-review.googlesource.com);
`origin` here is the GitHub mirror (`git remote -v`, README.md). A GitHub PR is imported into Gerrit, with
the PR title and first comment becoming the commit subject and body (.github/PULL_REQUEST_TEMPLATE).
Every commit on master carries a `Change-Id:` and `Reviewed-on: https://go-review.googlesource.com/...`
trailer (`git log -5`).

## Commit rejected for Signed-off-by line or Markdown
Go does not use `Signed-off-by`; Gerrit and GitHub bots enforce the CLA instead. Commit messages are
`pkg/path: lowercase verb phrase`, no trailing period, no Markdown, body wrapped at ~72 columns,
`Fixes #N` / `Updates #N` for issues (.github/PULL_REQUEST_TEMPLATE, https://go.dev/wiki/CommitMessage).

## Question filed as a GitHub issue gets closed
The golang/go issue tracker is for bugs and proposals only; questions go to golang-nuts, the Go Forum,
Gophers Slack (.github/SUPPORT.md, README.md). Security bugs go to security@golang.org (CONTRIBUTING.md).

## Test passes locally but fails on LUCI builders because GOROOT is read-only
GOROOT may not be writable on builders, so tests must write to a temp dir, not GOROOT
(commit 115f2c3673). See ISS-1 for a change reverted over this.

## go test fails with "no space left on device" on our CI runners
Our CI runners' /tmp is tmpfs capped at 512 MB (infra, reported 2026-09-24); large temp files from `go
test` or `go build` exhaust it. cmd/go's builder work dir (`src/cmd/go/internal/work/action.go`
`NewBuilder`) and `testing.T.TempDir` (`src/testing/testing.go`) both call `os.MkdirTemp(GOTMPDIR, ...)`,
so setting `GOTMPDIR=/scratch/gotmp` on those runners redirects both without code changes.
