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

## DEC-2 — keep `net.retry` default at 3 for our internally shipped cargo (`MAX_RETRY_DEFAULT`, src/util/network/retry.rs:82)
Why: raising it to 5 last quarter let cargo silently absorb a 40-minute mirror outage instead of the failures reaching our alerts.
Rejected: raising default to 5 — masks outages by retrying through them instead of surfacing the failure
Reverse if: alerting is changed to detect prolonged retry activity independent of final success/failure
Date: 2026-09-24 (team meeting; code confirmed unchanged, no commit)
