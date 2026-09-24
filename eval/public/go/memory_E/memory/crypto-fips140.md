# Crypto and the FIPS 140 module

## Purpose
`crypto/...` public packages are largely thin wrappers over `crypto/internal/fips140/...`, a
self-contained module that is snapshotted and submitted for FIPS 140 validation.

## Location
- `src/crypto/internal/fips140/` — the module: `aes`, `sha256/512/3`, `hmac`, `hkdf`, `drbg`,
  `ecdsa`, `ed25519`, `mlkem`, `mldsa`, `rsa`, `nistec`, `bigmod`, `tls12/13`, `ssh`, ...
- `src/crypto/internal/fips140deps/` — the only bridge from the module to other internal packages
  (`byteorder`, `cpu`, `godebug`, `time`).
- `src/crypto/internal/{fips140only,fips140test,fips140hash,boring,...}` — mode enforcement,
  CAST/ACVP tests, BoringCrypto (`GOEXPERIMENT=boringcrypto`).
- `lib/fips140/` (repo root) — frozen module snapshots (`v*.zip`), `fips140.sum` checksums, and
  alias files (`inprocess.txt`, `certified.txt`) naming the version each alias selects. Zips are
  produced by `src/cmd/go/internal/fips140/mkzip.go`; recipes in `lib/fips140/Makefile`.

## Important Constraints
- The module's imports are fenced by `crypto/internal/fips140deps.AllowedInternalPackages`
  ("DO NOT add new packages here just to make the tests pass") and by the fips140 section of
  `src/go/build/deps_test.go`. Reason: any internal API the module imports is locked for the
  lifetime of a validated module, which can be years.
- Never edit files under `lib/fips140/` by hand; they are checksummed snapshots.
- Watch for accidental dependency growth (e.g. `crypto/internal/boring` pulling in more of
  `fips140/aes/gcm` than needed was fixed in 41fd3e5b1b).
