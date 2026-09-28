---
name: project-retry-max-delay
description: "In-progress task adding configurable net.retry-max-delay config key; step 1 done, step 2 (wiring into retry.rs) pending"
metadata:
  node_type: memory
  type: project
  originSessionId: 0fb02de4-307e-400e-b3e5-f01f0581d6aa
  modified: 2026-09-28T07:24:24.774Z
---

Adding a new `net.retry-max-delay` config key (seconds) to make the maximum retry backoff configurable. Plan:
1. DONE (2026-09-28) — added `retry_max_delay: Option<u64>` to `CargoNetConfig` in src/context/schema.rs.
2. PENDING — use it in src/util/network/retry.rs (`Retry::new`, `next_sleep_ms`, and the Retry-After cap) instead of the hardcoded `MAX_RETRY_SLEEP_MS`. Default must stay 10 seconds when unset. Do not touch the jitter logic.
3. PENDING — document the key in the config reference and add a unit test.

**Why:** paused after step 1 at the user's request; resuming step 2 later.

**How to apply:** when picking this back up, read the value via `net_config()` rather than a raw env var — see [[feedback-config-via-net-config]] for why that matters here specifically.
