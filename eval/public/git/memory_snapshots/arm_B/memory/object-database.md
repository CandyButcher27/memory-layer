# Object database (ODB)

## Purpose
Reading and writing Git objects through a pluggable "source" abstraction, with alternates,
replace refs, commit-graph and an in-memory overlay.

## Location
- `odb.[ch]` — `struct object_database`, top-level API (`odb_new`, `odb_read_object`, ...)
- `odb/source.[ch]` — `struct odb_source` vtable + `odb_source_new()`
- `odb/source-files.[ch]` — default backend; composes `source-loose` + `source-packed`
- `odb/source-loose.[ch]`, `object-file.[ch]`, `loose.[ch]` — loose objects
- `odb/source-packed.[ch]`, `packfile.[ch]`, `packfile-list.[ch]`, `midx*.c` — packs, MIDX
- `odb/source-inmemory.[ch]` — objects that are readable but never persisted
- `odb/transaction.[ch]` — batched writes / pack ingestion; `odb/streaming.[ch]` — streams

## Architecture
- `struct object_database` (owned by a `struct repository`) keeps a linked list of sources:
  the primary (usually `$GIT_DIR/objects`, where writes go) first, then alternates from
  `objects/info/alternates` / `GIT_ALTERNATE_OBJECT_DIRECTORIES` (read-only). A hashmap keyed
  by path rejects duplicate registrations (case-insensitive when `core.ignoreCase`).
- `struct odb_source` is a vtable: `read_object_info`, `read_object_stream`, `for_each_object`,
  `count_objects`, `find_abbrev_len`, `freshen_object`, `write_object`, `write_object_stream`,
  `begin_transaction`, `read_alternates`, `write_alternate`, `optimize`, `optimize_required`,
  `generate_pack`, `fsck`, plus `free`/`close`/`create_on_disk`/`prepare`.
- Types: `files`, `loose`, `packed`, `in-memory`. `odb_source_new()` always builds a `files`
  source today; `loose`/`packed` are sub-sources of it. Backend structs embed `base` first and
  are reached with `*_downcast()` helpers that `BUG()` on a type mismatch.
- `odb->inmemory_objects` is an in-memory source for a small number of objects that must be
  readable but not written (e.g. browse-only callers).
- Only one `odb_transaction` may be pending at a time (`odb->transaction`).
- `odb_set_temporary_primary_source()` swaps the write target (used for quarantine dirs).

## Testing
- Unit: `t/unit-tests/u-odb-inmemory.c`; integration tests across `t/t1xxx`, `t/t5xxx` (pack).

## Important Constraints
- Go through the `odb_*` / source vtable API; don't reach into `packed_git` lists or loose
  paths from callers when an ODB function exists.
- Compat-hash (dual SHA-1/SHA-256) object mapping requires the Rust build (see
  `memory/build-and-rust.md`).
