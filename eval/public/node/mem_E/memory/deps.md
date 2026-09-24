# Vendored dependencies (`deps/`)

## Purpose
Third-party code built into the binary: V8, libuv (`uv`), OpenSSL, ICU (`icu-small`), llhttp,
nghttp2/ngtcp2, c-ares, zlib, brotli, zstd, sqlite, libffi, simdjson, ada (URL), undici (fetch),
amaro (TypeScript stripping), acorn, npm, corepack, LIEF/postject (SEA), perfetto, Rust `crates`,
and smaller libraries (`nbytes`, `ncrypto`, `merve`, `histogram`, `uvwasi`, `googletest`).

## Location
- `deps/<name>/` — sources plus the `.gyp`/`.gypi` that builds them.
- `tools/dep_updaters/update-<name>.sh|.mjs` — scripted updates; `tools/dep_updaters/README.md`
  documents procedures. Maintaining docs: `doc/contributing/maintaining/`.

## Important Constraints
- **Don't hand-edit vendored deps** except via their updater script, or — for V8 — as a
  deliberate floating patch.
- **V8 floating patches**: any change under `deps/v8/` must bump `v8_embedder_string`
  (`common.gypi`, currently `-node.N`) so the binary identifies the patched V8.
- JS deps that end up inside the binary are listed in `library_files` in `node.gyp` and appear to
  core code as `internal/deps/...` ([[build]], [[bootstrap]]).
- Each can be swapped for a system library with `./configure --shared-<name>`, so core code must
  not rely on internals of the vendored copy.
