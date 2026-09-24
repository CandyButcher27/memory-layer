# External systems
<!-- Only what the code cannot tell you: provider quirks, deferred constraints, what the deploy runs,
which credentials reach what, environment traps. Move a topic to its own file once it passes ~40 lines. -->

Last verified: 2026-09-23

## PR to a stable/X.Y branch fails "Check commit prefix"
On django/django, a PR whose base is `stable/X.Y` must have its title and every commit subject start with `[X.Y]`,
or the `check-commit-prefix` job fails. Source: .github/workflows/check_commit_messages.yml (re-read 2026-09-23).
