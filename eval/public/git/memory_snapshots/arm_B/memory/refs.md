# References and ref storage backends

## Purpose
Storage and transactional update of refs and reflogs, behind a pluggable backend interface.

## Location
- `refs.[ch]` — public API, backend registry (`refs_backends[]`), migration between formats
- `refs/refs-internal.h` — `struct ref_storage_be` vtable and `struct ref_store`
- `refs/files-backend.c` — loose ref files + reflogs; delegates packed refs to
  `refs/packed-backend.c` (`packed-refs` file) via its own `packed_ref_store`
- `refs/reftable-backend.c` — adapter onto the `reftable/` library
- `refs/iterator.c`, `refs/ref-cache.[ch]`, `refs/debug.c` (tracing wrapper)
- `reftable/` — standalone reftable format library (block, record, table, merged, stack, writer)

## Architecture
- `enum ref_storage_format` (`repository.h`): `FILES`, `REFTABLE`. Default is `FILES`, or
  `REFTABLE` when built with `WITH_BREAKING_CHANGES` (Git 3.0).
- `struct ref_storage_be` callbacks: init/release, create/remove_on_disk, transaction
  prepare/finish/abort, optimize(_required), rename/copy, iterator_begin, read_raw_ref,
  read_symbolic_ref, reflog iteration/exists/create/delete/expire, fsck.
- `refs_be_packed` exists as a backend struct but is only used internally by the files backend,
  not selectable as a repository format.
- `reftable/` includes only its own headers; `reftable/system.[ch]` is the single bridge to Git
  (`compat/posix.h`, zlib, `reftable_fsync`). Public headers are `reftable/reftable-*.h`.

## Configuration
- Repository format via `extensions.refStorage`; `git init --ref-format`, `git refs migrate`
  (`REPO_MIGRATE_REF_STORAGE_FORMAT_DRYRUN` / `_SKIP_REFLOG` flags in `refs.h`).
- Tests: `GIT_TEST_DEFAULT_REF_FORMAT` (defaults to `files` in `t/test-lib.sh`); CI has a
  `linux-reftable` / `linux-reftable-leaks` job.

## Testing
- Unit (clar): `t/unit-tests/u-reftable-*.c` with `lib-reftable.[ch]`.
- Integration: `t/t14xx` (refs), `t/t0610`-range reftable tests; run relevant scripts with
  both `GIT_TEST_DEFAULT_REF_FORMAT=files` and `=reftable`.

## Important Constraints
- Changes to backend-agnostic behaviour must work for both backends.
- Don't add Git-internal includes to `reftable/` outside `system.[ch]`.
