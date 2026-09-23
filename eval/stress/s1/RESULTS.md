# S1 and S4 results

Run 2026-09-24 on Windows 11. `uv run --no-project --with pytest pytest test_memlayer_stress.py` (uv picked
CPython 3.12.11; the ad hoc probes used 3.11.9 and behaved the same). CLI tests run `memlayer.py` in a
subprocess with `PYTHONUTF8`/`PYTHONIOENCODING` removed, which is how Git Bash or Claude Code runs it.
Result: 16 passed, 12 failed (28 cases, including the extra variants marked `b`). `memlayer.py` was not modified.
No model calls, so model cost is $0.

## Summary

| ID | Result | Evidence |
|---|---|---|
| S1.01 | pass | Second `init` prints "already initialised, nothing to do". Second `index` prints "index already current". All files byte-identical |
| S1.02 | partial | CRLF+BOM prose kept byte-for-byte and block appended once. This works only because Windows text mode writes CRLF. An LF `CLAUDE.md` (S1.02b) has every prose line rewritten to CRLF |
| S1.03 | pass | CRLF memory file gives `contains: alpha trap; beta trap` with no `\r` in the line |
| S1.04 | pass | 7 headings (backticks, `→`, `—`, `— contains:`, emoji, Japanese, Cyrillic) index correctly, and the rerun is a byte-identical no-op. Extra S1.04b fails: a heading that contains `` `memory/old.md` `` makes `check` report a dangling pointer |
| S1.05 | fail | `DB.md` and `api.v2.notes.md` work. `My Notes.md` is never indexed, and `check` still says clean |
| S1.06 | fail | `memory/sub/x.md` with an index line: not indexed, not reported, and the docs don't say nesting is unsupported. `check`: "memory layer clean" |
| S1.07 | pass | Both lines get `— contains: shared trap` |
| S1.08 | fail | `- Old note → \`memory/external.md\`` in user prose above the block is rewritten with `— contains: a trap` |
| S1.09 | fail | Invalid date: `ValueError` traceback. Future date: clean. Two dates: only the first is read, so clean |
| S1.10 | fail | A complete entry whose repro has a fenced `# run with debug` line is flagged. Other formats are handled correctly |
| S1.11 | pass | 40 files × 15 headings: CLI `index` takes 0.24 s. `CLAUDE.md` is 40,447 B (65 lines), `STATE.md` 445 B. `check` is clean |
| S1.12 | fail | Empty dir and missing `memory/` exit cleanly. A read-only `CLAUDE.md` gives a `PermissionError` traceback in `init` and in `index` |
| S1.13 | partial | Path `my proj ü 日本 — x`: `init`, `index` and `check` all work. Extra S1.13b fails: `check` crashes with `UnicodeEncodeError` as soon as its output contains a character outside cp1252 |
| S1.14 | pass | Exit 1 with "CLAUDE.md: missing, run init" and "STATE.md: missing, run init". No traceback. `ISSUES.md`, `decisions.md` and `memory/external.md` are not reported as missing |
| S4.1 | partial | Two branches that each rewrite `STATE.md` conflict in one 24-line hunk (Open threads through Last session). Git forces a manual merge, which is the right outcome. But `check` reports clean while the conflict markers are still in the file, and `@STATE.md` loads them into every session |
| S4.2 | measured | At S1.11 scale the auto-loaded context is about 40.9 KB, roughly 10.2k tokens per model call. That is more than the largest measured saving per session, so it no longer pays for itself. See below |
| S4.3 | partial | Only `index` reads headings, and nothing else refers to them. But `check` never notices an index that has gone stale, so a rename without `index` leaves check clean |

## Failures

### S1.02b: LF `CLAUDE.md` rewritten to CRLF on Windows
- Input: `CLAUDE.md` = `b"# My project\nKeep this \xe2\x80\x94 exactly.\n- rule one\n"`, then `memlayer.py init`.
- Output: the file starts `b"# My project\r\nKeep this \xe2\x80\x94 exactly.\r\n- rule one\r\n\r\n<!-- memory-layer:start -->..."`. Every line changes, so the git diff covers the whole file. `index` does the same, and so does every `init` on Windows (the seeded files come out CRLF). On Linux the reverse happens: a CRLF file becomes LF.
- Root cause: memlayer.py:21 (`read_text` converts newlines to `\n`) and memlayer.py:41 / :56 (`write_text` writes `os.linesep`).
- Fix: read with `read_bytes().decode("utf-8")` and write with `write_bytes(s.encode("utf-8"))`, keeping the file's own line ending (detect `\r\n` in the original and use it for the block).

### S1.04b: a heading that mentions a memory path creates a false "does not exist" error
- Input: `memory/x.md` with heading `` ## moved from `memory/old.md` `` and an index line for it. `check` is clean, then `index`, then `check`.
- Output: `['CLAUDE.md: points to memory/old.md, which does not exist']`
- Root cause: memlayer.py:81 collects `memory/*.md` references from all of `CLAUDE.md`, including the `— contains:` text that `index` generated.
- Fix: collect references from `INDEX_LINE` group 2 only, or strip `— contains: .*` before the `findall`.

### S1.05: a memory file name with a space is silently ignored
- Input: `memory/My Notes.md` (with `Last verified:` and `## odd name trap`), plus the index line ``- When testing → `memory/My Notes.md` ``. Then `index` and `check`.
- Output: the index line gets no `contains:`. `check` returns `[]`.
- Root cause: memlayer.py:16 `[\w.-]+` does not match a space, so `index` skips the line. memlayer.py:74 `rel not in claude` is a substring test, so `check` treats the file as indexed.
- Fix: in `check`, count a file as indexed only if it is in `{m[2] for m in INDEX_LINE.finditer(claude)}`. A spaced name would then be reported.

### S1.06: nested memory files are not indexed, not reported, and not documented
- Input: `memory/sub/x.md` with `## nested trap`, plus the index line ``- When testing → `memory/sub/x.md` ``.
- Output: `index` leaves the line unchanged. `check` prints "memory layer clean", exit 0. `SKILL.md`, `AGENTS.md` and the block never mention nesting.
- Root cause: memlayer.py:69 `glob("*.md")` is not recursive, and memlayer.py:16 / :81 `[\w.-]+` excludes `/`.
- Fix: use `rglob("*.md")` in `check` and report any nested file as "nested memory files are not supported".

### S1.08: index-shaped user prose outside the block is rewritten
- Input: `CLAUDE.md` = ``# Mine\n- Old note → `memory/external.md`\n``, then `init`, add `## a trap` to `memory/external.md`, then `index`.
- Output: the prose line becomes ``- Old note → `memory/external.md` — contains: a trap``.
- Root cause: memlayer.py:54 `INDEX_LINE.sub(fill, text)` runs over the whole file, not just the managed block.
- Fix: run the substitution only on the slice between `<!-- memory-layer:start -->` and `<!-- memory-layer:end -->`.

### S1.09: bad `Last verified:` dates
- Invalid. Input: `memory/x.md` = `# x\nLast verified: 2026-13-45\n` (indexed). `memlayer.py check` output:
  ```
  File "...memlayer.py", line 79, in check
    elif (age := (date.today() - date.fromisoformat(m[1])).days) > STALE_DAYS:
  ValueError: month must be in 1..12
  ```
- Future. Input: `Last verified: 2099-01-01`. Output: "memory layer clean", exit 0.
- Two dates. Input: `Last verified: 2026-09-24\nLast verified: 2020-01-01`. Output: "memory layer clean", exit 0.
- Root cause: memlayer.py:79 has no guard on `fromisoformat` and checks only `age > STALE_DAYS`, so a negative age passes. memlayer.py:76 `VERIFIED.search` reads only the first match.
- Fix: wrap the parse in `try/except ValueError` and report "invalid date". Report `age < 0` as "date in the future". Use `findall` and report more than one date.

### S1.10: a `#` line inside a fenced block splits an issue entry
- Input: `ISSUES.md` with `## ISS-3 — complete with fenced repro` / `Symptom: script fails` / ```` ```bash ```` / `# run with debug` / `./x.sh` / ```` ``` ```` / `Cause: CRLF`.
- Output: `"ISSUES.md: 'ISS-3 — complete with fenced repro' needs Symptom: and Cause:"` is flagged, although the entry has both fields. The rest is handled correctly: ISS-2 and ISS-5 (`## ISS-5:` style) are flagged, and ISS-1, `### ISS-4`, `## Bug:` and `**Symptom:**` bold fields are not.
- Root cause: memlayer.py:85 `re.split(r"^(?=#+ )", ...)` splits on any line starting with `#`, including shell comments and Python tracebacks inside code fences.
- Fix: split on `^(?=## )`, or strip fenced blocks (`` ```.*?``` ``, `re.S`) the same way `COMMENT` is stripped at memlayer.py:84.

### S1.12: a read-only `CLAUDE.md` gives a traceback
- Input: `CLAUDE.md` = `# Mine\n` with the read-only attribute set (`os.chmod(..., S_IREAD)`), then `memlayer.py init <dir>`.
- Output: a traceback ending `File "...memlayer.py", line 41, in init ... PermissionError: [Errno 13] Permission denied: '...\\ro\\CLAUDE.md'`. The four seeded files were already created, so the run leaves a half-initialised project.
- Same for `index` with a read-only `CLAUDE.md` and a pending update: a traceback at `line 56, in index ... PermissionError`.
- Root cause: memlayer.py:41 and memlayer.py:56, where the writes are unguarded.
- Fix: catch `OSError` in `main()` and print `cannot write <path>: <reason>` with exit 1. Better, check that `CLAUDE.md` is writable before creating the seeded files.
- Notes (not failures): `index` on an empty directory prints "index already current", which is misleading because there is no `CLAUDE.md`. `init` on a mistyped path (`probe/does/not/exist`) silently creates the whole directory tree (memlayer.py:34 `mkdir(parents=True)`). A non-UTF-8 `CLAUDE.md` (cp1252 `café`) makes `init` raise `UnicodeDecodeError` (memlayer.py:21).

### S1.13b: `check` crashes on non-ASCII output
- Input: in the project `日本 proj`, add `memory/日本.md` (not indexed), then `memlayer.py check` with stdout piped, as Claude Code runs it.
- Output: `File "...memlayer.py", line 132, in main  print(...)  UnicodeEncodeError: 'charmap' codec can't encode characters in position 7-8`.
- It also reproduces with ASCII paths: an `ISSUES.md` entry titled `## ISS-1 — retry → loop` with no `Cause:` crashes `check` the same way (`'→'`). `→` is the character the layer's own index lines use.
- Root cause: memlayer.py:132 (and :126, :129) print through `sys.stdout`, which is cp1252 on a Windows pipe.
- Fix: `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` at the start of `main()`.

### S1.14 note
The run passes as specified, but only `CLAUDE.md` and `STATE.md` are checked for existence (memlayer.py:62 iterates `CAPS`). A project missing `ISSUES.md` or `decisions.md` is reported clean.

## S4.1: parallel sessions and `STATE.md` on merge

Method: a temp git repo with a `STATE.md` base written from `templates/STATE.md`. Branch `wt-a` closes a session that fixed ISS-7: Broken becomes "none known" and Open threads, Next 3 and Last session are rewritten. Branch `wt-b` closes a session that added a Hindi OCR pack: Open threads, Next 3 and Last session are rewritten. Both branches set the same `Last updated:`. Then `git merge wt-a` (fast-forward) and `git merge wt-b`.

Result: `CONFLICT (content): Merge conflict in STATE.md`, one hunk of 24 lines per side, from `## Open threads` through the whole `## Last session`. Git auto-merged the non-overlapping parts: Broken took A's "none known", which is correct here. `Last updated` merged because both sides had the same value. Resolving it takes a human or model rewrite of Open threads, Next 3 and Last session, since the two handoffs can't both hold. Every parallel close rewrites Last session, so every parallel pair conflicts. That is safer than a silent merge.

Risks:
- With the markers still in place, `memlayer.py check` printed "memory layer clean" (exit 0; 43 lines, under the cap). `@STATE.md` would load the `<<<<<<<` markers and both handoffs into every session. Suggested fix: `check` flags `^<<<<<<< |^=======$|^>>>>>>> ` in `STATE.md`, `CLAUDE.md` and `memory/*.md`.
- Sections that auto-merge are taken without any semantic check. If A had removed a Broken item while B edited a non-adjacent section, git would take both edits silently. That is usually right for "now only" state, but nothing checks it.

## S4.2: auto-loaded context size vs. session cost

| Scale | `CLAUDE.md` | `STATE.md` | Total | ≈ tokens (bytes/4) |
|---|---|---|---|---|
| Fresh `init` | 1,927 B | 445 B | 2,372 B | ~0.6k |
| S1.11 (40 files × 15 headings, ~55-char headings) | 40,447 B | 445 B (template; ~3–4 KB at the 60-line cap) | ~40.9–44 KB | ~10.2k–11k |

Each fully indexed file adds about 960 B (~240 tokens) to `CLAUDE.md`. `check` does not flag the S1.11 file: it is 65 lines against a 100-line cap (memlayer.py:11, :66), and the cap counts lines, not bytes. That size also sits at Claude Code's large-memory warning threshold of about 40k characters (from product knowledge, not measured here).

Comparison with `EVALUATION.md`: per-session input is 165k–170k tokens on the retrieval tasks and 110k–136k on recall. These totals include cache and are summed over about 5–6 tool calls, so about 6–7 model calls. The auto-loaded context is sent again on every call, so at S1.11 scale it costs about 10.2k × 6.5 ≈ 66k input tokens per session. That is about 40% of a 165k session. The largest measured saving from the layer was 26k per session (recall, E→F). The retrieval saving was 5k (A→D). So at S1.11 scale the index costs 2.5× to 13× what it saves in tokens.

Break-even: the budget is the saving divided by about 6.5 calls, so 0.8k–4k tokens (3–16 KB) of auto-loaded context. Subtract the ~2.4 KB base and that leaves room for roughly 1–14 fully indexed files at S1.11 density. Most calls are cache reads, billed at about 10% of the input rate, so the dollar break-even is several times higher. A cap of about 16 KB (4k tokens) on block + `STATE.md` is a defensible limit for "cheap". `check` would need a byte cap to enforce it.

## S4.3: renaming headings

Read and grep of `memlayer.py`, `SKILL.md`, `commands/session-close.md` and `templates/`: headings are read only by `index()` (memlayer.py:50-52). Nothing links to a heading: there are no `file.md#anchor` references, and `ISSUES.md` / `decisions.md` entries are referenced by ID. `session-close.md:100` names the heading only in the session's report. So `index` is the only thing that must rerun, and `SKILL.md:80-81` says so.

Gap: renaming `## old trap name` to `## renamed trap` without rerunning `index` leaves ``— contains: old trap name`` in `CLAUDE.md`, and `check` still prints "memory layer clean". `check` (memlayer.py:60-88) never compares the `contains:` text against the current headings. Suggested fix: in `check`, run the `index` substitution in memory and report "index stale, run index" if the text would change.
