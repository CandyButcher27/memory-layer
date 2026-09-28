---
name: project-clean-p-stale-rmeta
description: "Investigation into `cargo clean -p foo` leaving stale .rmeta files when foo is a renamed dependency"
metadata:
  node_type: memory
  type: project
  originSessionId: 853a2575-340f-46e7-9363-77ea750b5b78
  modified: 2026-09-28T07:28:27.672Z
---

Bug report: `cargo clean -p foo` leaves stale `.rmeta` files behind when `foo` is depended on
via `bar = { package = "foo" }`. Investigated in `src/ops/cargo_clean.rs`, 2026-09-28.

Ruled out by user: release-profile directory logic (repros in debug too), file locking
(repros with a single cargo process).

Findings so far:
- The name-matching itself (`pkg.name()` at cargo_clean.rs:356, `target.crate_name()` at
  cargo_clean.rs:374-376) only ever reads the package's own name/target — verified via
  `compute_metadata()` in `src/compiler/build_runner/compilation_files.rs:743` that a
  dependent's rename alias never feeds into the unit's metadata hash or output filename.
  So plain rename-vs-match logic is probably NOT the root cause.
- Stronger lead: `clean_specs` (cargo_clean.rs:196-229) builds `layouts` (excludes Host
  whenever a `--target` is resolved, including via `build.target` config fallback) vs
  `layouts_with_host` (always includes Host). Fingerprint/custom-build cleanup use
  `layouts_with_host`; the regular artifact-removal loop (line 382, where `.rmeta`/`.rlib`
  get matched) uses `layouts` only. A package built for the host (typical for a renamed
  build-dependency/proc-macro) under an explicit/configured `--target` would have its
  fingerprint deleted but its host `deps/` artifacts never visited — matching the reported
  symptom (fingerprint gone, `.rmeta` stale).

**Why:** user is planning to write a failing testsuite case starting from the rename-vs-match
angle before checking the layouts/host-exclusion angle.
**How to apply:** if a rename-only testsuite case passes (doesn't reproduce), point back to
the `layouts` vs `layouts_with_host` split and suggest a case with a renamed build-dependency
plus explicit `--target` instead.
