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

## DEC-2 — Do not build with WITH_BREAKING_CHANGES (keeps reftable non-default in our builds)
Why: our backup tooling rsyncs .git/refs/ and packed-refs directly; under reftable those paths don't hold the refs, so backups would silently capture nothing. Default is picked at compile time in repository.h:25-29 (`REF_STORAGE_FORMAT_DEFAULT` — `reftable` iff `WITH_BREAKING_CHANGES` is defined, else `files`), then applied per-repo in setup.c:2803-2821 (explicit --ref-format > GIT_DEFAULT_REF_FORMAT env > init.defaultRefFormat config > REF_STORAGE_FORMAT_DEFAULT). Upstream stages reftable-as-default under Git 3.0 (see DEC-1's WITH_BREAKING_CHANGES pattern in BreakingChanges.adoc).
Rejected: patching REF_STORAGE_FORMAT_DEFAULT directly — leaves us diverged from upstream's macro and easy to lose on a merge; not defining the build macro is a build-config choice, no source patch needed.
Reverse if: backup tooling is changed to use `git for-each-ref`/`git pack-refs`-safe backup instead of raw filesystem rsync of refs/packed-refs.
Date: 2026-09-23 (checked against repository.h and setup.c at a27268a3ad)
