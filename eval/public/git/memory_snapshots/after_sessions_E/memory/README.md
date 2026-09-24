# Project memory index

Per-subsystem notes for the Git source tree. Read the relevant file before changing that area,
then verify against the code — code wins on any disagreement.

| File | Covers | Read before |
|---|---|---|
| [build-and-rust.md](build-and-rust.md) | Make + Meson dual build, `NO_RUST`/`WITH_RUST`, `src/` Rust crate, `WITH_BREAKING_CHANGES` | adding files, touching build flags or Rust code |
| [object-database.md](object-database.md) | `odb.[ch]`, `odb/` source vtable, loose/packed/in-memory backends, alternates, transactions | object read/write, packfile, alternates work |
| [refs.md](refs.md) | `refs.[ch]`, `refs/` backends (files, packed, reftable), `reftable/` library | ref/reflog/transaction changes |
| [testing.md](testing.md) | `t/` shell tests, `test-tool`, clar unit tests, lint gates, CI sanitizers | writing or running tests |
| [project_ref-format-default-policy.md](project_ref-format-default-policy.md) | Fork decision: keep `FILES` as default ref storage, not reftable, this year | touching `WITH_BREAKING_CHANGES`, ref-format defaults, or backup tooling assumptions |
| [transport-http-protocol-v2.md](transport-http-protocol-v2.md) | `remote-curl.c` HTTP protocol v2 negotiation via the `Git-Protocol` header, and v0 fallback consequences | debugging smart-HTTP protocol version issues, proxy header stripping, `ls-refs`/fetch v2 capability loss |

## Not yet mapped
Large areas with no memory file yet: index/`read-cache.c`, diff/`xdiff/`, merge-ort, protocol v2
command internals (`connect.c`, `fetch-pack.c`, `upload-pack.c` — the HTTP header negotiation
layer is covered in transport-http-protocol-v2.md, but not these), config, `builtin/` command
dispatch (`git.c`), trace2, `compat/`. Add a file when work in one of them yields knowledge a
cold session would need.

## When to add a file
Only for a substantial subsystem a future session should read before touching it. Small facts
go into the closest existing file. Update this index whenever files are added, renamed, merged
or removed.
