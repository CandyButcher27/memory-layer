# Node.js core — working notes for Claude

This is the Node.js runtime source (`main` branch; version in `src/node_version.h`).
C++ in `src/`, JavaScript in `lib/`, vendored libraries in `deps/`, tests in `test/`,
docs in `doc/`, build and lint tooling in `tools/`.

## Project memory

Component knowledge lives in `memory/` (index: `memory/README.md`).

- **Before substantial work**: read `memory/README.md` and the relevant `memory/*.md`. Then
  inspect the actual code before trusting memory — code is the source of truth.
- **After every major change window** (a feature, a significant bug fix, an
  architecture/API/pipeline/dependency change, a substantial refactor, a completed debugging
  investigation — not a trivial edit): update the affected `memory/*.md`; create a new memory
  file for a new substantial subsystem; update `memory/README.md`; correct stale claims in place
  rather than leaving them beside new ones.
- Never mention `memory/` in commits, PRs, code comments, or docs — state the underlying fact.

## Workflow

- `/think` — for non-obvious design work, use it before committing to an approach
- Build: `./configure && make -j$(nproc)` → `out/Release/node`. `lib/` is compiled into the
  binary, so JS changes need a rebuild before tests see them (see `memory/build.md`).
- Test: `tools/test.py <path-or-glob>`; `make test-only` for the default suites; `make cctest`
  for C++ (see `memory/testing.md`).
- Lint: `make lint` (or `lint-js`, `lint-cpp`, `lint-md`); `make format-cpp` for C++ formatting.
- Changes to public behaviour need matching updates in `doc/api/`; new CLI flags go in
  `doc/api/cli.md` and `doc/node.1`; new error codes in `doc/api/errors.md`.

## Project rules to respect

- `lib/` code uses primordials and `internal/errors` codes (`memory/lib-conventions.md`).
- Every C++ function exposed to JS is registered as an external reference, or the snapshot build
  breaks (`memory/native-bindings.md`).
- Changes under `deps/v8/` bump `v8_embedder_string` in `common.gypi`; other deps are updated
  only through `tools/dep_updaters/`.
- Commit messages: `subsystem: imperative description`, first line ideally ≤ 50 chars, never > 72; body wrapped at 72
  (`doc/contributing/pull-requests.md#commit-message-guidelines`).
- AI policy (`doc/contributing/ai-guidelines.md`): don't remove or modify existing tests without
  human verification; don't put for-profit AI brand names in commit messages (PR description
  only, if at all); pull requests must not be opened by automated tooling.
- This file is ignored by the project's `.gitignore` ("Rules for AI assistants"); it stays local.
