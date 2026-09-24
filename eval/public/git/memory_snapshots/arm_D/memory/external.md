# External systems
<!-- Only what the code cannot tell you: provider quirks, deferred constraints, what the deploy runs,
which credentials reach what, environment traps. Move a topic to its own file once it passes ~40 lines. -->

Last verified: 2026-09-23

## Patches go to the mailing list, not GitHub pull requests
git/git on GitHub does not take pull requests. Code, review and bug reports go to git@vger.kernel.org;
GitGitGadget (https://gitgitgadget.github.io/) turns a GitHub PR into mailing-list patches. For a
single-commit PR, leave the description empty: the commit message is the description.
Source: .github/PULL_REQUEST_TEMPLATE.md, README.md, Documentation/SubmittingPatches.
Security issues go privately to git-security@googlegroups.com (README.md).

## `make` fails when cargo/rustc is not installed
Since 2.55 Rust is on by default in both build systems (Makefile `ifndef NO_RUST`, meson `rust`
option default `enabled`). Without a Rust toolchain, build with `make NO_RUST=YesPlease` or
`meson configure -Drust=disabled`. The option goes away in Git 3.0 (see DEC-1 in decisions.md).
Source: Makefile "Optional Rust support" comment; meson_options.txt; Documentation/BreakingChanges.adoc.
