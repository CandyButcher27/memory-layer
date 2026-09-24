# C++ bindings layer (`src/`)

## Purpose
Exposes native functionality (libuv, OpenSSL, V8 APIs, deps) to `lib/` through
`internalBinding('<name>')`.

## Location
- `src/node_binding.cc`: `NODE_BUILTIN_STANDARD_BINDINGS(V)` list of all builtin bindings.
- `src/node_external_reference.h`: `EXTERNAL_REFERENCE_BINDING_LIST_*` lists.
- `src/node_snapshotable.{h,cc}`: snapshot (de)serialization of bindings.
- `src/node_options.{h,cc}`: all CLI options.
- Core types: `Environment` (`env.h`), `Realm` (`node_realm.h`), `BaseObject`
  (`base_object.h`), `AsyncWrap` (`async_wrap.h`), `IsolateData`.
- Style: `doc/contributing/cpp-style-guide.md`; fast API calls:
  `doc/contributing/adding-v8-fast-api.md`.

## Architecture: adding or changing a binding
A binding file (see `src/node_os.cc` for a small example) ends with:
```cpp
NODE_BINDING_CONTEXT_AWARE_INTERNAL(os, node::os::Initialize)
NODE_BINDING_EXTERNAL_REFERENCE(os, node::os::RegisterExternalReferences)
```
and the name must also appear in `NODE_BUILTIN_STANDARD_BINDINGS` (node_binding.cc) and the
external-reference list (node_external_reference.h). **Every C++ function exposed to JS must be
registered as an external reference**, otherwise snapshot building fails — the snapshot needs
stable addresses for all callbacks. Per-isolate templates use
`NODE_BINDING_PER_ISOLATE_INIT`.

Bindings that keep state across the snapshot must be serializable (see the
`SERIALIZABLE_BINDING_TYPES` machinery in `node_snapshotable.h`); stateless ones are simply
re-initialized.

## CLI options
- Declared as fields in `src/node_options.h` (`DEFINE_BOOL_FIELD(x) = default`) and registered in
  `node_options.cc` via `AddOption("--flag", "help", BOOL_FIELD(x), kAllowedInEnvvar, <default>)`.
  Boolean options automatically accept `--no-` negation.
- Read from JS with `getOptionValue('--flag')` (`lib/internal/options.js`).
- Every new option must be documented in `doc/api/cli.md` **and** `doc/node.1`; enforced by
  `test/parallel/test-cli-node-options-docs.js` (and
  `test-process-env-allowed-flags-are-documented.js` for `kAllowedInEnvvar` options).

## Important Constraints
- Code guarded by feature macros (`HAVE_OPENSSL`, `HAVE_INSPECTOR`, `HAVE_FFI`, ...) must still
  compile when the feature is off; the matching JS modules are put on the `cannot_be_required`
  list in `src/node_builtins.cc` ([[bootstrap]]).
- C++ is linted with `make lint-cpp` (cpplint + `tools/checkimports.py`) and formatted with
  `make format-cpp` (clang-format on the diff).
