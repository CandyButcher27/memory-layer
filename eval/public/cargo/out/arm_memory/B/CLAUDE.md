# CLAUDE.md

This repo is **Cargo**, the Rust package manager (library `cargo` at `src/lib.rs`, binary at
`src/bin/cargo/`), plus its helper crates under `crates/` and `credential/`.

Note the layout: the library's top-level modules live directly under `src/` (`src/compiler`,
`src/workspace`, `src/resolver`, `src/sources`, `src/ops`, `src/context`, `src/diagnostics`,
`src/util`). There is no `src/cargo/core/` tree; don't assume upstream-era paths.

## Commands

- Full suite: `cargo test` (slow). Targeted: `cargo test --test testsuite -- <module>::<test>`
- Update snapshot expectations: `SNAPSHOTS=overwrite cargo test --test testsuite -- <filter>`
- Other workspace crates: `cargo test --workspace --exclude cargo --exclude benchsuite --exclude resolver-tests`
- Schemas: `cargo test -p cargo-util-schemas -F unstable-schema` (checks `*.schema.json`)
- Resolver property tests: `cargo test -p resolver-tests`
- Lint/format (CI-enforced): `cargo fmt --all --check`, `cargo clippy --workspace --all-targets --no-deps`
- Docs/man: `cargo lint-docs --check` (lint docs in `doc/book/src/reference/lints.md`),
  `cargo build-man` after editing `doc/man/*.md` (generated output in `etc/man/` and `doc/`)

## Rules

- `std::env::var*` is disallowed — read env through `GlobalContext::get_env`/`get_env_os`.
  `std::collections::HashMap/HashSet`, `IndexMap/IndexSet` are disallowed — use
  `crate::util::data_structures::*`. File locking goes through `crate::util::flock`. See `clippy.toml`.
- New user-visible behavior is gated as unstable first (`src/workspace/features.rs`:
  `cargo-features` for `Cargo.toml`, `-Z` for CLI/config) and documented in
  `doc/book/src/reference/unstable.md`.
- Commits are atomic; tests go in their own commit *before* the behavior change, passing and
  snapshotting current behavior, so the fix commit shows the diff in expected output.
  Commit subjects use `type(scope): ...` (e.g. `fix(builtin-deps): ...`).
- Changing a published crate under `crates/` or `credential/` needs a version bump
  (`ci/validate-version-bump.sh`).
- Contributor guide: `doc/contrib/src/` (architecture, tests, process). Cargo follows the
  rust-lang LLM usage policy (`doc/contrib/src/process/llm-usage.md`).

## Workflow

- `/think` — for non-obvious design work, use it before committing to an approach

## Project memory

`memory/` holds per-subsystem technical notes; `memory/README.md` is the index.

- **Before substantial work**: read `memory/README.md` and the relevant `memory/*.md`. Memory can
  be stale — inspect the actual code before trusting it; the code wins.
- **After every major change window** (a feature, a significant bug fix, an
  architecture/API/pipeline/dependency change, a substantial refactor, a completed debugging
  investigation — not a trivial edit): update the affected `memory/*.md`; create a new memory file
  for a new substantial subsystem; update `memory/README.md`; correct stale claims in place rather
  than leaving them beside new ones.
- Never reference `memory/` in commits, PRs, code comments, or docs — state the underlying fact.
