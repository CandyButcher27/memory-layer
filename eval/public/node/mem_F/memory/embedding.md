# Embedders: several Environments, C++ standard, platform ownership
<!-- Traps that only show up when Node.js is embedded, not in `node` itself. -->

Last verified: 2026-09-24

## Range-for over queue.Lock().PopAll() deadlocks when built as C++23
Node.js builds with `-std=gnu++20` (common.gypi), but embedders may compile it as C++23. Under
C++23 (P2718R0) the lock temporary in a range-for initializer lives until the loop ends, so the
mutex stays held while tasks run. Pop into a local first, then iterate. Source: 32d23ec931, ISS-1.

## Second Environment aborts because a per-isolate template was set per Environment
`embedding.md` allows several Environments on one `IsolateData`. A template stored with a
CHECK-empty setter from a per-Environment binding initializer aborts the second one; build it once
per isolate and reuse it. Source: 1105aec934, ISS-3. Tests live in test/cctest/test_environment.cc.

## Process-wide statics break when two Environments are alive
Anything static per process (inspector debug-signal `uv_async_t`, watchdog thread) must be
per-Agent or set up once per process. Source: 5859ced229, ISS-4.

## FreeEnvironment() blocks JavaScript for sibling Environments on the same isolate
Source: 6dfe4eb0f0, ISS-2.

## Features missing when the embedder owns the V8 platform or inspector
With `kNoInitializeNodeV8Platform` there is no tracing agent; with `kNoCreateInspector` there is no
parent inspector handle. Throw an `ERR_*_UNAVAILABLE`/`ERR_INSPECTOR_NOT_AVAILABLE` error instead
of CHECKing. Source: c636b05c9e (ISS-6), e98208bc27 (ISS-5).
