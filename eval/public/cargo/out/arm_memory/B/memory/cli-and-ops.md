# CLI and operations

## Purpose
`cargo <cmd>` argument parsing (clap) and dispatch to library operations.

## Location
- `src/bin/cargo/main.rs`, `cli.rs` — global flags, aliases, external `cargo-*` subcommands
- `src/bin/cargo/commands/<cmd>.rs` — one file per built-in command (`cli()` + `exec()`),
  registered in `commands/mod.rs` (`builtin()` and `builtin_exec()`)
- `src/util/command_prelude.rs` — shared arg helpers (`ArgMatchesExt::workspace`, compile opts)
- `src/ops/` — the real work; commands are thin wrappers (`cargo_compile`, `cargo_package`,
  `registry/` for publish/login/owner/yank/search, `cargo_add`, `cargo_fix`, `cargo_tree`, …)

## Adding or changing a command/flag
- New flags that change behavior go behind `-Z unstable-options` or a `-Z` flag first.
- Update the man page source `doc/man/cargo-<cmd>.md`, then `cargo build-man` (regenerates
  `etc/man/` and `doc/book/src/commands/`); CI's `ci/validate-man.sh` fails otherwise.
- Each command has `--help` UI snapshot tests in `tests/testsuite/cargo_<cmd>/help/`.
- Guide: `doc/contrib/src/implementation/subcommands.md`.
