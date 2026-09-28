---
name: project-build-std-decision
description: Decision to not enable -Zbuild-std for internal CI builds due to runner cache size doubling
metadata:
  node_type: memory
  type: project
  originSessionId: e8a98360-935a-4635-8b65-66e8a945dc5d
  modified: 2026-09-28T07:23:37.057Z
---

Decided against enabling `-Zbuild-std` for internal builds: it doubled the CI runner cache size, from 40 GB to 80 GB.

**Why:** build-std compiles `core`/`std`/etc. from source per build config, which multiplies cached artifacts on the runners.

**How to apply:** If build-std comes up again (e.g. someone proposes enabling it, or asks about its cache footprint), surface this prior decision and the cache-size cost before recommending it. The relevant code is `resolve_std`/`generate_std_roots` in `src/compiler/standard_lib.rs`, wired in via `cargo_compile/mod.rs` (flag parsing) and `unit_dependencies.rs`/`unit_graph.rs` (graph construction).

Related, but separate: the crates.io block for CI started in 2026-07 (not August as originally said) — noted as a correction, context for that block otherwise not captured here.
