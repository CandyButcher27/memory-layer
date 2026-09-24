# Module loaders (CJS + ESM)

## Purpose
Load user code: `require()`, `import`, `import()`, and the customization hooks that intercept both.

## Location
`lib/internal/modules/`:
- `cjs/loader.js` — `Module`, `Module._load`, `Module._resolveFilename`, `Module._extensions`,
  `wrapModuleLoad`, `loadESMFromCJS` (the `require(esm)` path).
- `esm/loader.js` — `ModuleLoader` class, cascaded loader (`getOrInitializeCascadedLoader`),
  `register()`.
- `esm/resolve.js`, `esm/load.js`, `esm/translators.js` (format → module record, including
  CJS-as-ESM), `esm/module_job.js` (`ModuleJob`, `ModuleJobSync`), `esm/module_map.js`
  (`LoadCache`, `ResolveCache`), `esm/get_format.js`, `esm/utils.js`.
- `esm/hooks.js` + `esm/worker.js` — async hooks on a separate worker.
- `customization_hooks.js` — synchronous in-thread hooks (`registerHooks`).
- `package_json_reader.js` (backed by a C++ reader), `helpers.js` (compile cache, etc.),
  `typescript.js` (type stripping via `deps/amaro`), `run_main.js` (entry-point dispatch).
- Public surface: `lib/module.js` attaches `register`, `registerHooks` (set in cjs/loader.js),
  `findPackageJSON`, compile cache and source-map APIs onto `Module`.

## Architecture
- The two loaders are intertwined: `esm/loader.js` imports `kIsExecuting`/`kRequiredModuleSymbol`
  from `cjs/loader.js`, and there's an explicit comment about avoiding a `esm/resolve` ↔
  `cjs/loader` cycle. Watch for load-order cycles when adding requires.
- `require(esm)`: `Module.prototype._compile` routes `format === 'module'` to
  `loadESMFromCJS()`, which evaluates the ESM graph synchronously (`ModuleJobSync`). Graphs with
  top-level await throw `ERR_REQUIRE_ASYNC_MODULE` (`esm/module_job.js`).
- **Two hook systems**:
  - `module.registerHooks()` — synchronous, runs in-thread, applies to both `require` and
    `import` (`resolveWithHooks` / `loadWithHooks` in `customization_hooks.js`).
  - `module.register()` / `--import` loaders — asynchronous, run on a dedicated loader-hook
    worker thread (`AsyncLoaderHookWorker`), with the main thread blocking on shared memory via
    `Atomics` for synchronous callers.
- Initialization is done from `pre_execution.js` (`initializeCJS`, `initializeESM`), see
  [[bootstrap]].

## Testing
`test/es-module/`, `test/module-hooks/`, plus many `test/parallel/test-module-*`,
`test-require-*`. Fixtures live under `test/fixtures/es-modules/` and similar.

## Important Constraints
- Error codes and resolution behaviour are spec'd in `doc/api/esm.md`, `doc/api/modules.md`,
  `doc/api/packages.md`, `doc/api/module.md`; behaviour changes need matching doc updates.
