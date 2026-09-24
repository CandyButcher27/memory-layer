# Decisions
<!-- One short entry per choice someone might argue again:
"## DEC-<n> — <choice>" heading, then
Why:
Rejected: <alternative> — <reason>
Reverse if: <condition that would change the answer>
Date:
Never edit an old entry's reasoning. Add a new one and mark the old "Superseded by DEC-<m>". -->

## DEC-1 — Buffer.poolSize default (64 KiB) stays unbackported to v22 LTS
Why: TSC call 2026-09-24: the extra ~56 KiB RSS per realm from raising the default (8192 -> 65536, landed v26.3.0/v24.18.0 via PR #63597) hurts embedders that create many realms/workers. v22 keeps the 8192 default. Defined at lib/buffer.js:188; documented at doc/api/buffer.md, "Buffer.poolSize" section (YAML changes block cites PR #63597, v26.3.0/v24.18.0 only).
Rejected: backporting to v22 LTS — rejected because of the per-realm RSS cost for embedders.
Reverse if: the RSS-per-realm cost is mitigated (e.g. lazy pool allocation) or embedders stop citing it as a blocker.
Date: 2026-09-24
