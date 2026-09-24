# State
<!-- Now only. Overwritten every session. Finished work leaves. Cap 60 lines. -->

Goal: Node.js, an open-source, cross-platform JavaScript runtime environment (README.md)

## Deployed
Latest release commit on this branch: 342bf6d669 — 2026-09-23, Version 22.23.3 'Jod' (LTS)

## Broken
- none known

## Open threads
- none

## Next 3
1. 
2. 
3. 

## Last session
Branch: main
Uncommitted: none
Stopped at: corrected Jenkins AIX RAM figure in memory/external.md (16 GB, not 4 GB, per Build WG); confirmed neither tools/test.py nor the Makefile picks test parallelism based on memory (Makefile passes -j/JOBS through as-is; tools/test.py falls back to multiprocessing.cpu_count() when unset, tools/test.py:1500-1504; the only memory knob is TestCase.max_virtual_memory, a per-test RLIMIT_AS cap, unrelated to job count) — no code change (investigation only)
Tried, failed: 
Resume with: 

Last updated: 2026-09-24
