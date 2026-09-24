# Decisions
<!-- One short entry per choice someone might argue again:
"## DEC-<n> — <choice>" heading, then
Why:
Rejected: <alternative> — <reason>
Reverse if: <condition that would change the answer>
Date:
Never edit an old entry's reasoning. Add a new one and mark the old "Superseded by DEC-<m>". -->

## DEC-1 — Rust becomes a mandatory build dependency in Git 3.0
Why: staged rollout so distributors can prepare; Rust parts are "test balloons" until then. 2.52 auto-detect in Meson, 2.55 default-on in both build systems (Makefile `ifndef NO_RUST`, meson_options.txt `rust` default `enabled`), 3.0 build option removed. Source: Documentation/BreakingChanges.adoc.
Rejected: keeping Rust optional indefinitely — to be judged by how painful the optional path is to maintain.
Reverse if: evaluation finds significant impact on downstream distributions; then the mandatory step may be deferred past 3.0 (BreakingChanges.adoc). The last pre-3.0 release becomes an LTS.
Date: 2026-09-23 (checked against Documentation/BreakingChanges.adoc and Makefile at e7476ba542)
