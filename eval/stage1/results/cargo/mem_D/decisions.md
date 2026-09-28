# Decisions
<!-- One short entry per choice someone might argue again:
"## DEC-<n> — <choice>" heading, then
Why:
Rejected: <alternative> — <reason>
Reverse if: <condition that would change the answer>
Date:
Never edit an old entry's reasoning. Add a new one and mark the old "Superseded by DEC-<m>". -->

## DEC-1 — `cargo install` uses the package's `Cargo.lock` by default
Why: install could resolve different versions than the author built and tested with, and fail; Cargo team decision on issue #7169. Implemented in 7941be6fb (#17388). `--locked` is now a no-op kept for compatibility; with no packaged lockfile, deps resolve normally.
Rejected: keep ignoring the lockfile unless `--locked` — users get untested dependency versions
Reverse if: the Cargo team revisits #7169
Date: 2026-09-11

## DEC-2 — Not enabling `-Zbuild-std` for internal builds
Why: doubled the sccache cache size on CI runners, from 40 GB to 80 GB.
Rejected: enabling `-Zbuild-std` — cache growth too costly given the runners' 50 GB sccache cap
Reverse if: runner cache limits increase substantially or build-std's cache footprint shrinks
Date: 2026-09-28
