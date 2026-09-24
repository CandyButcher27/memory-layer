# Conventions for JavaScript in `lib/`

## Purpose
Rules that every change to the JS side of core must follow; most are enforced by custom ESLint
rules in `tools/eslint-rules/`.

## Primordials
- `lib/` code must not call mutable globals/prototype methods directly (user code could have
  patched them). Use frozen copies from `primordials` (`ArrayPrototypePush(arr, x)`,
  `SafeMap`, `SafeSet`, `PromisePrototypeThen`, ...), destructured at the top of the file.
- Enforced by `prefer-primordials`; destructure lists are kept sorted (`alphabetize-primordials`).
- Created in `lib/internal/per_context/primordials.js`. Guidance, including performance caveats
  (e.g. avoid `SafeArrayIterator`-heavy patterns on hot paths): `doc/contributing/primordials.md`.
- Objects used as dictionaries use `{ __proto__: null }` (`set-proto-to-null-in-object`,
  `prefer-proto`).

## Errors
- Throw via `require('internal/errors').codes.ERR_*`, never bare `new Error(...)` for API errors.
- New codes are defined with `E('ERR_X', message, BaseClass)` in `lib/internal/errors.js`,
  kept alphabetical (`alphabetize-errors`), and **must be documented in `doc/api/errors.md`**
  (`documented-errors`). See `doc/contributing/using-internal-errors.md`.
- Deprecations: `DEP####` codes must be documented in `doc/api/deprecations.md`
  (`documented-deprecation-codes`).
- Argument validation helpers live in `lib/internal/validators.js`.

## Module layout
- Public modules are `lib/<name>.js`; implementation goes in `lib/internal/`. Internal modules are
  not reachable from user code (only with `--expose-internals`, used by tests).
- C++ is reached via `internalBinding('<name>')` ([[native-bindings]]).

## Documentation that must move with code
- API changes: `doc/api/<module>.md`, with a YAML `added:`/`changes:` block
  (`added: REPLACEME` for new APIs — the releaser fills in versions).
- New CLI flags: `doc/api/cli.md` and `doc/node.1`.
- Style: `doc/contributing/api-documentation.md`, `doc/contributing/writing-docs.md`.

## Lint
`make lint-js` (ESLint config `eslint.config.mjs`, rules in `tools/eslint-rules/`),
`make lint-md` for docs, `make lint` for everything. ESLint is installed on demand under
`tools/eslint/`.
