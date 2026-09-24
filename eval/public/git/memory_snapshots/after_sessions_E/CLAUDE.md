# CLAUDE.md

This is the upstream Git source tree (C, with an optional Rust library in `src/`).
Contribution norms live in `Documentation/SubmittingPatches`, `Documentation/CodingGuidelines`
and `Documentation/ReviewingGuidelines.adoc` — follow them; they override general habits.

## Commands

- Build: `make` (add `DEVELOPER=1` for the strict warning set used in CI). Meson is also
  supported: `meson setup build && meson compile -C build`.
- Build without Rust: `make NO_RUST=1` / `meson setup -Drust=disabled`.
- Integration tests: `cd t && sh ./t0001-init.sh -v -i` for one script, `make -C t` for all.
- Unit tests (clar): `make unit-tests`.
- Test lint: `make -C t test-lint` (chainlint, greplint, meson test-list check).

## Working rules

- Every new `.c` source, builtin, test script (`t/tNNNN-*.sh`) or unit suite
  (`t/unit-tests/u-*.c`) must be registered in **both** `Makefile` and the relevant
  `meson.build`; `make -C t check-meson` fails otherwise.
- New code takes a `struct repository *` parameter; `the_repository` is only visible to files
  that `#define USE_THE_REPOSITORY_VARIABLE`.
- Behaviour that changes defaults for Git 3.0 goes behind `WITH_BREAKING_CHANGES`.
- `reftable/` is a self-contained library; only `reftable/system.[ch]` may reach into Git proper.
- Commits need a `Signed-off-by:` trailer (DCO), per `Documentation/SubmittingPatches`.

## Workflow

- `/think` — for non-obvious design work, use it before committing to an approach

## Project memory

`memory/` holds per-subsystem notes on how this codebase actually works. `memory/README.md` is
the index.

**Before substantial work:** read `memory/README.md` and the `memory/*.md` files relevant to the
area you are touching. Then inspect the actual code before trusting a memory claim — code is the
source of truth.

**After every major change window** — a feature, a significant bug fix, an
architecture/API/pipeline/dependency change, a substantial refactor, or a completed debugging
investigation (not a trivial edit):

- update the affected `memory/*.md`;
- create a new memory file if a new substantial subsystem appeared;
- update `memory/README.md` when files are added, renamed, merged or removed;
- correct stale claims in place rather than adding a new fact beside a contradictory old one.

Never mention `memory/` in commits, patches, code comments or user-facing docs; state the
underlying project fact instead.
