# Issues
<!-- Append-only, one entry per bug:
"## ISS-<n> — <title>" heading, then
Symptom: exact error text or observed behavior
Cause: root cause
Fix: commit hash
Test: the test that fails without the fix
Status: open | fixed -->

## ISS-1 — fields.W225 "null has no effect on GeneratedField." is a false warning
Symptom: system check warns `fields.W225: null has no effect on GeneratedField.` on a GeneratedField declared with `null=` (Django 6.1).
Cause: the check added in 6025eab3c5 (#36806) assumed `null` is ignored by GeneratedField; ticket #37348 showed the warning is incorrect (docs/releases/6.1.2.txt).
Fix: fb32a564cc (reverts 6025eab3c5; fields.W225 stays documented as removed in docs/ref/checks.txt)
Test: none added; the revert removed the W225 tests from tests/invalid_models_tests/test_ordinary_fields.py
Status: fixed
