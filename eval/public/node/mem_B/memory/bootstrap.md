# Startup / bootstrap

## Purpose
How a `node` process goes from `main()` to running user code, and which builtin modules user code
may load.

## Location
- C++: `src/node_main.cc` → `src/node.cc` (`Start`, `LoadSnapshotData`, `StartExecution`),
  `src/node_main_instance.cc` (`CreateMainEnvironment`), `src/node_realm.cc`
  (`PrincipalRealm::BootstrapRealm`), `src/api/environment.cc` (embedder/worker paths).
- JS: `lib/internal/bootstrap/` (`realm.js`, `node.js`, `web/`, `switches/`, `shadow_realm.js`),
  `lib/internal/per_context/` (`primordials.js`, `domexception.js`, `messageport.js`),
  `lib/internal/process/pre_execution.js`, `lib/internal/main/*.js`.

## Architecture
Order of execution for the main thread:
1. **per_context** scripts run for every V8 context (primordials are created here).
2. **`internal/bootstrap/realm`** creates the loaders: `process.binding`, `internalBinding`,
   and `BuiltinModule` (the internal module system for `lib/`).
3. **`PrincipalRealm::BootstrapRealm`** runs `internal/bootstrap/node`, then
   `web/exposed-wildcard` + `web/exposed-window-or-worker` (skipped with
   `no_browser_globals`), then one of `switches/is_main_thread` / `is_not_main_thread`, then one of
   `switches/does_own_process_state` / `does_not_own_process_state`.
   Steps 1–3 are captured in the build-time snapshot ([[build]]), so they run at build time, not
   per process — no runtime state (env vars, CLI flags, cwd) may be baked in here.
4. **`StartExecution`** (`src/node.cc` ~line 340) picks one `internal/main/*` script:
   worker → `worker_thread`; `node inspect` → `inspect`; `--help` → `print_help`;
   `--prof-process`; `-e` without `-i` → `eval_string`; `--check`; `--bench`; `--test`;
   `--watch`; a positional script (or `--vfs-load`) → `run_main_module`; TTY stdin or `-i` →
   `repl`; else `eval_stdin`. Adding a CLI mode means adding a branch here and a `main/` script.
5. Each `internal/main/*` script calls `prepareMainThreadExecution()` (or
   `prepareWorkerThreadExecution()`) from `pre_execution.js`. `prepareExecution()` is where
   runtime-dependent setup belongs: flags, warnings, permission model, diagnostics channel,
   experimental module enabling, and module-loader initialization (`initializeCJS`,
   `initializeESM`).

## Builtin module visibility (`lib/internal/bootstrap/realm.js`, `src/node_builtins.cc`)
- `src/node_builtins.cc` `GetBuiltinCategories()` decides `cannot_be_required`: everything under
  `internal/bootstrap/`, `internal/per_context/`, `internal/deps/`, `internal/main/`, modules for
  compiled-out features, and **experimental/deprecated public modules** (`bench`, `dtls`, `ffi`,
  `quic`, `sqlite`, `stream/iter`, `vfs`, `wasi`, `zlib/iter`, `sys`, ...).
- In `realm.js`: `schemelessBlockList` = modules only reachable via `node:` (e.g. `node:test`,
  `node:sqlite`, `node:sea`, `node:ffi`, `node:vfs`); `experimentalModuleList` = modules hidden
  until enabled at run time.
- Enabling happens in `pre_execution.js` `setup<Feature>()` functions via
  `BuiltinModule.allowRequireByUsers(id)` guarded by `getOptionValue('--experimental-...')`.
  Some are default-on (`sqlite`, `ffi` when built with `HAVE_FFI`) and are disabled with
  `--no-experimental-*`.
- Adding a new experimental public module therefore touches: the lists in `realm.js`, the
  `cannot_be_required` list in `node_builtins.cc`, a `setup*()` in `pre_execution.js`, the option
  in `src/node_options.{h,cc}`, and docs (`doc/api/cli.md`, `doc/node.1`).

## Important Constraints
- Only the main thread owns process state; workers take the `does_not_own_process_state` path.
- ShadowRealms get their own allow list via `BuiltinModule.setRealmAllowRequireByUsers` in
  `shadow_realm.js`.
