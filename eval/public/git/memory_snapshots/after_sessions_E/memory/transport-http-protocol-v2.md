---
name: transport-http-protocol-v2
description: How the smart-HTTP client negotiates protocol v2 via the Git-Protocol header, and what breaks if that header is stripped in transit
metadata:
  type: project
---

## How v2 negotiation over HTTP actually works

`remote-curl.c` never assumes v2 is in effect locally. Version selection is a round trip:

- `get_protocol_version_config()` (remote-curl.c:477) picks the locally-configured desired
  version, then `get_protocol_http_header()` (remote-curl.c:397) turns it into a
  `Git-Protocol: version=2` request header (`GIT_PROTOCOL_HEADER`, environment.h:63), added to
  the `info/refs?service=...` discovery request (remote-curl.c:504) and to the RPC POST for
  the service itself (remote-curl.c:971).
- Push-shaped services never send v2: remote-curl.c:500 forces `version = protocol_v0` whenever
  `service != "git-upload-pack"`, since push has no v2 wire form.
- The client's *effective* version is decided by re-parsing the server's response, not by what
  it asked for: `parse_git_refs()` calls `discover_version(&reader)` (remote-curl.c:249) on the
  actual bytes that came back. If the response isn't a v2 capability advertisement, the client
  silently runs the v0/v1 path (`get_remote_heads()`) regardless of local config.
- Server side (git-http-backend, and any compliant smart-HTTP server) only offers v2 if it saw
  the `Git-Protocol` request header — typically wired to `GIT_PROTOCOL` via
  `SetEnvIf Git-Protocol ".*" GIT_PROTOCOL=$0` (Documentation/git-http-backend.adoc:97).

**Consequence**: if a proxy strips the `Git-Protocol` header on the way to the server (this
happened with our corporate HTTP proxy), the server never sees the v2 request, so it replies
with the v0 advertisement, and the client falls back to v0 for that fetch — even though both
ends support v2 and local `protocol.version` config says v2. This is silent: no error, no
warning, just a v0 exchange. `git -c http.extraHeader='Git-Protocol: version=2' ...` or fixing
the proxy to pass the header through are the only fixes; there is no other side channel for HTTP
(unlike ssh/file, which use the `GIT_PROTOCOL` env var directly — see
Documentation/gitprotocol-v2.adoc:68-74).

## What is lost by falling back to v0 for fetch/ls-remote

Per Documentation/gitprotocol-v2.adoc (fetch-only; push is unaffected since it never uses v2):

- **`ls-refs` filtering** — v2 lets the client request only refs matching a `ref-prefix`
  (gitprotocol-v2.adoc:215-221). In v0 the server unconditionally dumps the *entire* ref
  advertisement before negotiation even starts, which is the classic pain point for repos with
  huge numbers of refs/branches.
- **Ref advertisement is otherwise skipped entirely** in v2 for operations that don't need it;
  v0 always pays for it up front (gitprotocol-v2.adoc:26).
- **`unborn` HEAD reporting** — v2-only `ls-refs` feature to learn about a symref pointing at an
  unborn branch (gitprotocol-v2.adoc:223-229).
- **Capabilities as a separate, extensible section** rather than packed behind a NUL byte on the
  first ref line — v0's capability list is smaller and less flexible, and things like the
  `agent` string move back to being a hidden extra (gitprotocol-v2.adoc:19-25, 178-195).
- **Stateless-friendly command framing** — v2 was designed so the http remote helper can act as
  a pure proxy per command; v0 does not have the same clean flush semantics
  (gitprotocol-v2.adoc:28-29, 170-176).
- Downstream of the above, features implemented as v2 `fetch` command extensions (partial
  clone filters, shallow/deepen refinements, packfile URIs, sideband-all, wait-for-done) are
  negotiated through v2's capability list; falling back to v0 means the client is limited to
  whatever v0 exposed for the same feature (often nothing, or a coarser form).

No memory file yet covers `connect.c`/`fetch-pack.c`/`upload-pack.c` internals of these
features — only the HTTP negotiation layer above. See [[README]] for the rest of the "not yet
mapped" transport area.
