# Project memory index

Per-subsystem notes for Cargo. Read the relevant file before changing that subsystem; verify
against the code. Module-level `//!` docs in the source are often the deepest reference — these
files point at them and record what isn't obvious.

| File | Covers | Read when |
|---|---|---|
| [compilation.md](compilation.md) | `ops::cargo_compile` → `BuildContext` → unit graph → `BuildRunner` → `JobQueue`, fingerprints, build scripts | Touching build/check/test/doc, rebuild detection, `target/` layout |
| [resolver.md](resolver.md) | Dependency resolver, feature resolver, `Cargo.lock` encoding | Touching resolution, features, lockfile, `cargo update` |
| [sources.md](sources.md) | `Source` trait, registry/git/path/directory/replaced sources, `SourceId` | Touching fetching, registries, git deps, vendoring, source replacement |
| [manifest-and-workspace.md](manifest-and-workspace.md) | `Cargo.toml` parsing, `Workspace`/`Package`, unstable feature gates, `cargo-util-schemas`, builtin deps | Adding/validating manifest fields, adding unstable features |
| [config.md](config.md) | `GlobalContext`, config files/env/`--config` deserialization | Adding config keys or env vars |
| [diagnostics.md](diagnostics.md) | Cargo lints and diagnostic passes | Adding a warning/lint |
| [cli-and-ops.md](cli-and-ops.md) | `src/bin/cargo` subcommands and their `ops::*` implementations | Adding/changing a subcommand or flag |
| [testing.md](testing.md) | `tests/testsuite`, `cargo-test-support`, snapshots, gated test categories | Writing or running tests |

## When to add a file

Only for a subsystem substantial enough that a future session should read it before editing it
(e.g. `cargo package`/`publish`, `cargo fix`, `cargo add`, global cache GC are not yet mapped).
Small facts go into the closest existing file.
