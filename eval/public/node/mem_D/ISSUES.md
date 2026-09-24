# Issues
<!-- Append-only, one entry per bug:
"## ISS-<n> — <title>" heading, then
Symptom: exact error text or observed behavior
Cause: root cause
Fix: commit hash
Test: the test that fails without the fix
Status: open | fixed -->

## ISS-1 — Foreground task flush hangs when Node.js is compiled as C++23
Symptom: embedder building Node.js with C++23 hangs in the first foreground task flush (deadlock on the task queue's non-recursive mutex)
Cause: `for (auto& task : queue.Lock().PopAll())` — C++23 (P2718R0) keeps the `Locked` temporary alive for the whole loop, so a task that posts to the same queue deadlocks
Fix: 32d23ec931 (PR #66066)
Test: none added in the commit
Status: fixed

## ISS-2 — "illegal access" in sibling Environments while one is freed
Symptom: timers and I/O callbacks of other Environments sharing the loop/isolate fail with an "illegal access" exception while `FreeEnvironment()` runs
Cause: `FreeEnvironment()` sets `DisallowJavascriptExecutionScope` on the whole isolate, then spins the shared loop in `CleanupHandles()`
Fix: 6dfe4eb0f0 (PR #65977)
Test: test/cctest/test_environment.cc
Status: fixed

## ISS-3 — Second Environment on the same IsolateData aborts on require('net')
Symptom: abort on a CHECK that a per-isolate template slot is empty; ffi/sqlite/dtls hit "FunctionTemplate already instantiated"
Cause: per-isolate templates were created in the per-Environment binding initializer
Fix: 1105aec934 (PR #65978)
Test: test/cctest/test_environment.cc
Status: fixed

## ISS-4 — Two Environments that own the inspector abort the process
Symptom: abort in `Agent::Start()` when two Environments with `kDefaultFlags` are alive at once; created one after another, each leaked a watchdog thread
Cause: one file-level static `uv_async_t` for the debug signal handler, re-initialized per Environment
Fix: 5859ced229 (PR #65877)
Test: test/cctest/test_environment.cc
Status: fixed

## ISS-5 — connectToMainThread() in a Worker aborts without a parent inspector
Symptom: abort on `CHECK_NOT_NULL(parent_handle_)` in `Agent::ConnectToMainThread()` when the parent was created with `kNoCreateInspector`
Cause: missing check; now throws `ERR_INSPECTOR_NOT_AVAILABLE`
Fix: e98208bc27 (PR #65976)
Test: test/cctest/test_environment.cc
Status: fixed

## ISS-6 — trace_events createTracing() aborts on an embedder-owned V8 platform
Symptom: `createTracing()` aborts and `getEnabledCategories()` dereferences null under `kNoInitializeNodeV8Platform`
Cause: no `tracing::Agent` exists; lib only checked `hasTracing` and `ownsProcessState`. Now throws `ERR_TRACE_EVENTS_UNAVAILABLE`
Fix: c636b05c9e (PR #65954)
Test: test/embedding/test-embedding-trace-events-unavailable.js
Status: fixed

## ISS-7 — --snapshot-blob with an empty, foreign or truncated file crashes
Symptom: assertion abort (`CHECK_EQ(magic, kMagic)`, `ReadFileSync()` item count) or out-of-bounds read on a truncated blob
Cause: `BlobDeserializer` trusted every length field; `ReadFileSync()` required one item
Fix: 5f77f955d7 (PR #65955)
Test: test/parallel/test-snapshot-invalid-blob.js
Status: fixed

## ISS-8 — http2 "Assertion failed: onread->IsFunction()" after session.destroy() in a 'stream' handler
Symptom: `Assertion failed: onread->IsFunction()` (issue #64850)
Cause: destroy from a 'stream' handler drains nextTick while nghttp2 is still in mem_recv; close is deferred, so later HEADERS in the same buffer create C++ streams with no JS wrapper
Fix: 0e32ee2114 (PR #65116)
Test: test/parallel/test-http2-session-destroy-stream-handler.js
Status: fixed

## ISS-9 — RSA/DSA wrong-passphrase test flakes under FIPS
Symptom: decoder error instead of the expected "bad decrypt" in test-crypto-rsa-dsa / test-tls-passphrase
Cause: keys were re-encrypted on each FIPS run; some ciphertexts decrypt with valid padding under the wrong password
Fix: be819d5470 (PR #65983)
Test: test/parallel/test-crypto-rsa-dsa.js, test/parallel/test-tls-passphrase.js
Status: fixed
