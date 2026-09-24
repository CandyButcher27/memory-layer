# Project memory index

Technical knowledge about how Node.js core's major subsystems work, for sessions starting cold.
Code is the source of truth: if a file here disagrees with the source, fix the file.

This checkout is `main` (`src/node_version.h` says 27.0.0-pre), even though recent commits include
a v22 release commit. Always read versions from `src/node_version.h`, not from `CHANGELOG.md` or
git log.

| File | Covers | Read before |
|---|---|---|
| [build.md](build.md) | `configure.py`/GYP/Make/Ninja, js2c embedding of `lib/`, snapshot, build outputs | Building, changing `node.gyp`/`configure.py`, wondering why a `lib/` edit has no effect |
| [bootstrap.md](bootstrap.md) | Process startup: `src/node.cc` → realm bootstrap → `pre_execution` → `internal/main/*`; builtin module visibility and experimental gating | Touching startup, adding a CLI mode, adding/gating a builtin module |
| [native-bindings.md](native-bindings.md) | C++ binding layer in `src/`: registration macros, external references, CLI options, snapshot constraints | Adding/changing an `internalBinding()` or a CLI flag |
| [module-loaders.md](module-loaders.md) | CJS loader, ESM loader, `require(esm)`, `module.registerHooks` (sync) vs `module.register` (async, hook worker) | Anything under `lib/internal/modules/` |
| [lib-conventions.md](lib-conventions.md) | Rules for JS in `lib/`: primordials, `internal/errors`, lint rules, docs that must change alongside code | Writing or reviewing any `lib/` change |
| [testing.md](testing.md) | `tools/test.py`, test dirs, `.status` files, `test/common` rules, cctest | Writing or running tests |
| [deps.md](deps.md) | Vendored `deps/`, updater scripts, V8 floating-patch rules | Touching anything under `deps/` |

## When to add a file

Add one only for a subsystem substantial enough that a future session would decide better after
reading it (e.g. `crypto`, `http`/`http2`, `quic`, `test_runner`, `inspector`, `permission` are not
yet mapped). Small facts go into the closest existing file. Update this index whenever files are
added, renamed, merged, or removed.
