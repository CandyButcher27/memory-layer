# Build system and Rust integration

## Purpose
Two parallel build systems (Make and Meson) produce `libgit.a`, the `git` binary, builtins,
test helpers and unit tests. An optional Rust static library (`gitcore`) is linked in.

## Location
- `Makefile`, `config.mak.uname` (platform defaults), `config.mak.dev` (`DEVELOPER=1` warnings)
- `meson.build`, `meson_options.txt`, per-dir `meson.build` (`src/`, `t/`, `t/helper/`, ...)
- Rust: `Cargo.toml` (crate `gitcore`, `staticlib`, edition 2018, rust-version 1.49),
  `build.rs`, `src/*.rs`, `src/cargo-meson.sh`

## Architecture
- Make: every object is listed explicitly (`LIB_OBJS +=`, `BUILTIN_OBJS +=`,
  `CLAR_TEST_SUITES +=`). Meson has its own explicit lists. They are kept in sync by hand;
  `t/Makefile`'s `check-meson` target verifies the test lists match the files on disk.
- Rust is **on by default** in both systems (Make: unless `NO_RUST`; Meson: `rust` feature
  defaults to `enabled`). The Makefile comment says it becomes mandatory with Git 3.0.
  The main CI build script (`ci/run-build-and-tests.sh`) still exports `NO_RUST` for some jobs.
- With Rust enabled, `-DWITH_RUST` is added and `varint.c` is dropped: `src/varint.rs` exports
  `decode_varint`/`encode_varint` via `#[no_mangle] extern "C"`. Those are currently the only
  Rust→C exports; `hash.rs` and `csum_file.rs` call *into* C (`git_hash_*`, `hashfd`, ...).
- `src/loose.rs` implements the storage↔compat object-ID map (`MapType`: Reserved, LooseObject,
  Shallow, Submodule) used for dual-hash (SHA-1/SHA-256 interop) repositories.
- Features gated on `WITH_RUST` in C: `repo_set_compat_hash_algo()` in `repository.c` dies with
  "compatibility hash algorithm support requires Rust" without it.
- Make builds the crate at `target/{debug,release}/libgitcore.a` (`DEBUG` selects debug);
  `RUST_TARGETS` supports cross builds and macOS universal libs via `lipo`.

## Configuration
- `WITH_BREAKING_CHANGES` → `-DWITH_BREAKING_CHANGES`; flips Git 3.0 defaults (e.g. reftable
  as default ref format, see `memory/refs.md`).
- `SANITIZE=leak` / `SANITIZE=address,undefined` are used by CI leak/asan jobs (`ci/lib.sh`).

## Important Constraints
- Adding a C file means editing both `Makefile` and `meson.build`.
- Rust must stay compatible with edition 2018 / rustc 1.49 as declared in `Cargo.toml`.
- A feature that needs Rust must degrade with a clear `die()` when built with `NO_RUST`.
