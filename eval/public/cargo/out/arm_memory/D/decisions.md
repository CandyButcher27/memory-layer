# Decisions
<!-- One short entry per choice someone might argue again:
"## DEC-<n> — <choice>" heading, then
Why:
Rejected: <alternative> — <reason>
Reverse if: <condition that would change the answer>
Date:
Never edit an old entry's reasoning. Add a new one and mark the old "Superseded by DEC-<m>". -->

## DEC-1 — `cargo install` honors the packaged `Cargo.lock` by default
Why: without it, installing a binary could resolve different dependency versions than were built and tested, so installs failed on packages that built fine (rust-lang/cargo#7169). Cargo team decision: https://github.com/rust-lang/cargo/issues/7169#issuecomment-4421296987
Rejected: ignore the lockfile unless `--locked` — the old behavior; `--locked` is now accepted but a no-op
Reverse if: the Cargo team revisits #7169
Date: 2026-09-11 (7941be6fb, PR #17388)
