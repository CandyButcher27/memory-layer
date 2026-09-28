---
name: project-typetracker-leading-zero-bug
description: "Investigation into CSV import bug where zero-padded strings (zip codes like 02134) get coerced to integers, dropping the leading zero"
metadata:
  node_type: memory
  type: project
  originSessionId: 9a47e4ff-f4d0-4abc-a8fe-ab5020f597d5
  modified: 2026-09-28T08:16:36.012Z
---

Bug: `sqlite-utils insert data.db items items.csv --csv` turns a zip-code column value like `02134` into the integer `2134`. Root cause located: `ValueTracker.test_integer` in `sqlite_utils/utils.py` (around line 470) uses `int(value)`, and Python's `int("02134")` happily returns `2134`, so `TypeTracker` (used by the CSV import path in `sqlite_utils/cli.py` around line 1267, on by default unless `--no-detect-types` is passed) misclassifies the column as integer.

User already ruled out (2026-09-28): not the `--alter` path (reproduces without it), not SQLite column affinity (value is already an int before reaching SQLite, confirmed in a debugger). Confirmed suspect: per-column type guessing in `TypeTracker`/`ValueTracker.test_integer`.

**Why:** silent, on-by-default type detection is destructive for any zero-padded numeric string (zip codes, phone extensions, IDs), not just this one case.

**How to apply:** Next session, user wants to write a failing test first (reproducing `02134` -> should stay `"02134"` text, not `2134`) before touching `test_integer`. Don't jump straight to a fix — follow their test-first approach. Likely fix direction discussed: reject strings with a leading `"0"` followed by another digit in `test_integer` so zero-padded values are left as text. Related to [[project_sample_option_rows]] in that both touch CSV/type-detection CLI behavior.
