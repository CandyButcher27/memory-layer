# Diagnostics and Cargo lints

## Purpose
User-facing warnings/errors; the ones with user-controllable levels (`[lints.cargo]`) are lints.

## Location
- `src/diagnostics/mod.rs` — policy docs (when to use a lint vs hard-coded diagnostic, message style)
- `src/diagnostics/lint.rs` — `Lint`, `LintGroup`, `LintLevel`
- `src/diagnostics/passes.rs` — passes, e.g. `emit_parse_diagnostics`
- `src/diagnostics/rules/` — one file per lint; `rules/mod.rs` holds `LINTS`, `LINT_GROUPS`,
  `PARSE_PASS_RULES`
- Rendering: `cargo-util-terminal` (`Shell`, `report::Report`, annotate-snippets)

## Adding a lint
- Pick the pass: manifest parse (`PARSE_PASS_RULES`), lockfile, pre-build unit graph, or
  post-build (`rules::unused_dependencies::lint_build_results`).
- Add to `LINTS` — sorted; unit tests in `rules/mod.rs` fail if unsorted or if a pass's lint is
  missing from `LINTS`.
- Only emit for local packages (except future-incompat); messages are lowercase phrases.
- Regenerate/verify docs: `cargo lint-docs` (writes `doc/book/src/reference/lints.md`; CI runs
  `--check`).

## Testing
`tests/testsuite/lints/` and `cargo test -p cargo --lib diagnostics`.
