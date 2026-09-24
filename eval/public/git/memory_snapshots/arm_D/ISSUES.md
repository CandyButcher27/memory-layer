# Issues
<!-- Append-only, one entry per bug:
"## ISS-<n> — <title>" heading, then
Symptom: exact error text or observed behavior
Cause: root cause
Fix: commit hash
Test: the test that fails without the fix
Status: open | fixed -->

## ISS-1 — `git ls-files -- <dir>/ ":(exclude)x"` wrongly excludes paths or reads out of bounds
Symptom: an exclude pathspec matches paths it shouldn't (non-excludes "a/b" "a/c" + exclude "x/b" drops "a/b/m"); with an exclude shorter than the common prefix, ASan reports an out-of-bounds read in match_pathspec_item()
Cause: common_prefix_len() computes the prefix from non-exclude items only, but match_pathspec_with_flags() stripped that prefix from exclude items too
Fix: 16abad3360 (follow-up b6f17686b2 restores the prefix optimization when an exclude comes first)
Test: t/t6132-pathspec-exclude.sh; t/unit-tests/u-dir.c
Status: fixed

## ISS-2 — t5616.47 flaky on macOS CI: "could not fetch <oid> from promisor remote"
Symptom: `fatal: ... The requested URL returned error: 500` then `fatal: could not fetch <oid> from promisor remote`
Cause: race in t/lib-httpd/apply-one-time-script.sh; concurrent requests could each run "one-time-script", returning several modified responses or an empty one
Fix: 5945464690
Test: t/t5567-one-time-script.sh
Status: fixed

## ISS-3 — CI "documentation" job: `gem: not found`
Symptom: `./ci/install-dependencies.sh: 23: gem: not found` after `gem install --version 1.5.8 asciidoctor`
Cause: Ruby was never installed explicitly; it used to arrive transitively via the asciidoc package, which stopped pulling it in
Fix: 4340a709bf
Test: none; the CI "documentation" job itself
Status: fixed
