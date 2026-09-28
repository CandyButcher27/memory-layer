# Decisions
<!-- One short entry per choice someone might argue again:
"## DEC-<n> — <choice>" heading, then
Why:
Rejected: <alternative> — <reason>
Reverse if: <condition that would change the answer>
Date:
Never edit an old entry's reasoning. Add a new one and mark the old "Superseded by DEC-<m>". -->

## DEC-1 — keep internal cargo build's default net.retry at 3, not 5
Why: raising it last quarter hid a 40-minute mirror outage from alerts (team meeting decision).
Rejected: raising MAX_RETRY_DEFAULT (src/util/network/retry.rs) to 5 — masks outages longer before alerting.
Reverse if: alerting is changed to fire on retry-exhaustion/latency directly instead of relying on fast failure.
Date: 2026-09-28
