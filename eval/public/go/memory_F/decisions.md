# Decisions
<!-- One short entry per choice someone might argue again:
"## DEC-<n> — <choice>" heading, then
Why:
Rejected: <alternative> — <reason>
Reverse if: <condition that would change the answer>
Date:
Never edit an old entry's reasoning. Add a new one and mark the old "Superseded by DEC-<m>". -->

## DEC-1 — Fork-built services run with GODEBUG=disablethp=1; runtime default is not patched
Why: Production hosts have transparent huge pages set to 'always'; several services showed RSS growth after the Go upgrade. Runtime lead decision. disablethp=1 makes sysMapOS call sysNoHugePageOS (MADV_NOHUGEPAGE) on new heap mappings; read at src/runtime/runtime1.go:309,366 (debug struct + godebugs table) and applied at src/runtime/mem_linux.go:187-189.
Rejected: patching the runtime default (debug.disablethp default `def:` unset/0) — avoided to keep the fork close to upstream; env var achieves the same effect per-service without a runtime source change.
Reverse if: upstream changes the kernel-THP-workaround default, or hosts move off THP=always.
Date: 2026-09-24