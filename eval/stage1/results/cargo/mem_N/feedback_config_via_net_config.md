---
name: feedback-config-via-net-config
description: "Don't read CARGO_NET_* env vars directly with std::env::var in retry.rs or similar — go through net_config() instead"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 0fb02de4-307e-400e-b3e5-f01f0581d6aa
  modified: 2026-09-28T07:24:19.909Z
---

Never read `CARGO_NET_*` (or other cargo config) env vars directly via `std::env::var(...)` inside implementation code like `src/util/network/retry.rs`. Always go through cargo's config system (e.g. `net_config()` / `CargoNetConfig`) instead.

**Why:** the user tried `std::env::var("CARGO_NET_RETRY_MAX_DELAY")` directly in retry.rs and it bypassed cargo's config layering — `--config` overrides and config files stopped working. Only the proper config path (`GlobalContext` → `net_config()`) correctly merges env vars, config files, and `--config` CLI overrides.

**How to apply:** when wiring any new `net.*` (or other) config key into behavior, read it off the deserialized config struct (e.g. `CargoNetConfig`) obtained via the context's config accessor, never via a raw env var lookup. Relevant to the in-progress [retry-max-delay task](project_retry_max_delay.md) step 2 (src/util/network/retry.rs).
