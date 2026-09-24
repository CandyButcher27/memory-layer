# Build system

## Purpose
Produces the `node` binary (plus `cctest`, `node_js2c`, `node_mksnapshot` helpers) from `src/`,
`lib/`, and vendored `deps/`.

## Location
- `configure` → `configure.py`: parses options, writes `config.gypi`, `icu_config.gypi`,
  `config.status`, and runs GYP (`tools/gyp_node.py`, gyp itself in `tools/gyp/`).
- `node.gyp`, `node.gypi`, `common.gypi`: GYP targets. `tools/v8_gypfiles/` builds V8.
- `Makefile` (Unix), `vcbuild.bat` (Windows), `BSDmakefile`.
- GN files (`BUILD.gn`, `*.gni`) exist for embedders building Node inside Chromium-style trees;
  see `doc/contributing/gn-build.md`. GYP is the primary build.
- Docs: `BUILDING.md`, `doc/contributing/building-node-with-ninja.md`.

## Common commands
```sh
./configure            # add --ninja to use Ninja, --debug for out/Debug too
make -j$(nproc)        # produces out/Release/node, symlinked as ./node
make test-only         # default test suites, no doc build
make lint              # JS, C++, markdown, doc linters
```
Outputs land in `out/Release/` (and `out/Debug/` with `--debug`). No build exists in a fresh
checkout; a full build compiles V8 and takes a long time.

## Architecture
- **js2c** (`tools/js2c.cc`, target `node_js2c`): every file in `lib/**/*.js` and the listed
  `deps/` JS files (`library_files` in `node.gyp`) is compiled into `node_javascript.cc`. The
  binary never reads `lib/` from disk at runtime, so **editing `lib/` requires a rebuild** to take
  effect. Exception: `./configure --node-builtin-modules-path=<dir>` makes the binary read builtins
  from disk (this also disables the snapshot and code cache — `configure.py` ~line 1970).
- **Startup snapshot**: `node_mksnapshot` runs the bootstrap JS at build time and serializes the
  heap into `node_snapshot.cc` (`src/node_snapshotable.cc`, `tools/snapshot/`). Controlled by
  `node_use_node_snapshot`; `--without-node-snapshot` falls back to `src/node_snapshot_stub.cc`.
  Consequence: bootstrap-time JS must be snapshot-safe (see [[bootstrap]], [[native-bindings]]).
- Optional features are compile-time switches that show up as C macros (`HAVE_OPENSSL`,
  `HAVE_INSPECTOR`, `HAVE_SQLITE`, `HAVE_FFI`, `HAVE_DTLS`, `OPENSSL_NO_QUIC`, ...). Both C++
  code and the builtin-module allow list in `src/node_builtins.cc` branch on them.
- `--shared-<dep>` options link system libraries instead of `deps/` copies.

## Important Constraints
- `.gitignore` ignores all dotfiles except an explicit allow list, plus `CLAUDE.md`. Check with
  `git check-ignore -v <path>` before assuming a new file is tracked.
- Python 3 is required for `configure` and `tools/test.py`.
