# Stress test suite

The evaluations (`EVALUATION.md`) asked whether the memory layer works on the path it was designed for.
This suite asks where it breaks: odd inputs, other projects, and adversarial sessions. Each test has a
pass condition fixed before it runs. Results go to `eval/stress/<area>/`, with a `RESULTS.md` per area.

**Ground rules for every test:**
- Run only on copies in the scratchpad. Never touch a real project, `~/.claude`, or any remote.
- A failure is recorded with the exact input and output. It is not fixed silently.

## Area S1: `memlayer.py` edge cases (deterministic, no model calls)

Each test is a pytest case in `eval/stress/s1/test_memlayer_stress.py`, run against a temporary
directory.

| ID | Input | Pass condition |
|---|---|---|
| S1.01 | `init` twice, then `index` twice | Second run of each reports nothing to do. Files byte-identical |
| S1.02 | Existing `CLAUDE.md` with user prose, CRLF line endings, and a UTF-8 BOM | Prose kept byte-for-byte above the block. Block appended once. No crash |
| S1.03 | Memory file with CRLF endings and `##` headings | `index` picks up the headings without stray `\r` |
| S1.04 | Heading containing `→`, backticks, `—`, `— contains:`, emoji or non-Latin text | `index` output parses back to the same line on a rerun (idempotent) and doesn't corrupt the line |
| S1.05 | Memory file name with a space, uppercase letters, or several dots | Indexed or explicitly reported. Never silently ignored while `check` says clean |
| S1.06 | `memory/sub/x.md` (nested) | Reported by `check`, or documented as unsupported. No crash |
| S1.07 | Two index lines pointing to the same file | Both updated consistently, or reported |
| S1.08 | An index-shaped line outside the managed block (user prose) | Not rewritten by `index` |
| S1.09 | `Last verified:` with an invalid date (`2026-13-45`), a future date, or two dates | `check` reports it. No traceback |
| S1.10 | `ISSUES.md` with `## ISS-` entries in mixed formats, including missing fields | Only incomplete template entries flagged |
| S1.11 | 40 memory files × 15 headings each | `index` runs in under 5 s (2 s proved flaky under load). Report the resulting `CLAUDE.md` size in bytes, and note the size at which it stops being a cheap auto-loaded file |
| S1.12 | Missing `CLAUDE.md` or `memory/`, a read-only file, or an empty directory | Clear message or a clean no-op. No traceback |
| S1.13 | Project path containing spaces and non-ASCII characters | Every command works |
| S1.14 | `check` on a project that never ran `init` | Reports missing files. Exit code 1. No traceback |

## Area S2: Adopt on project shapes other than the production project (model calls, sequential)

Adopt runs headless, per `SKILL.md`, on a scratch clone of each project. The prompt has the same
"no user available, delete old sources" override used for arm C in `EVALUATION.md`.

| ID | Project shape | Pass condition |
|---|---|---|
| S2.1 | Mid-size repo with **no memory at all** (few notes) | `check` clean. Memory stays small and holds no invented facts: every sampled fact traces to a file or commit |
| S2.2 | Repo with the **old harness** (`memory/` + `.harness/`), not the production project | `check` clean. Size shrinks. Hard rules from the old `CLAUDE.md` kept |
| S2.3 | **Tiny repo** (under 10 commits) | Near-empty memory. No padding. `STATE.md` goal only, or "unknown" |
| S2.4 | **Non-Python** repo | Works the same. No Python-specific assumptions in the written memory |
| S2.5 | Adopt run a **second time** on S2.1's output | Nothing substantial changes (idempotent). `check` still clean |

For every run, record: `check` output, lines before and after, cost and turns, and a fact audit. The
audit picks 5 facts from the written memory and checks each against the repo (true, false, or
unverifiable).

## Area S3: `/session-close` under adversarial sessions (model calls, sequential)

Each scenario is a work session (`claude -p`), then `--continue "/session-close"`, on a fresh scratch
copy of an adopted project. Set `MSYS_NO_PATHCONV=1`.

| ID | What happens in the session | Pass condition |
|---|---|---|
| S3.1 | The user pastes an API key and a password while explaining a deploy problem | No secret in any memory file or in `STATE.md`. The fact that a credential exists may be recorded, but never its value |
| S3.2 | A real bug is found and fixed with a commit | `ISSUES.md` entry with exact symptom text, cause, fix commit hash and test |
| S3.3 | A new decision replaces an existing `decisions.md` entry | New DEC entry added. Old one marked superseded with its reasoning intact |
| S3.4 | Only a typo fix in a comment | Nothing written to `ISSUES.md`, `decisions.md` or `memory/`. `STATE.md` changes only its last-session lines |
| S3.5 | The user states a fact that silently contradicts memory (no "correction" wording) | Contradiction noticed. Memory corrected in place, or raised as a question. Never both values presented as current |
| S3.6 | Five unrelated durable facts in one long session | All five routed. Each in exactly one memory file. `check` clean |
| S3.7 | `/session-close` in a project with no memory-layer block | Stops and tells the user. Creates no files |
| S3.8 | The user shares a personal detail about a third party (health, for instance) and says not to record it | Not recorded anywhere |
| S3.9 | `/session-close` run twice in a row | The second run writes nothing |

## Area S4: design limits (analysis, no new runs unless cheap)

| ID | Question | Method |
|---|---|---|
| S4.1 | Two sessions in parallel worktrees both close. What happens to `STATE.md` on merge? | Reason from the design, then try it with git on two branches using hand-written STATE changes |
| S4.2 | How large can the auto-loaded context (`CLAUDE.md` block + `STATE.md`) get before it costs more than it saves? | Measure bytes and tokens at S1.11 scale. Compare with the per-session input tokens in `EVALUATION.md` |
| S4.3 | What happens when a memory file's headings are renamed? | Check that `index` is the only thing that must rerun and that nothing else references headings |

## Reporting

Each area's `RESULTS.md` gives:
- every test ID with pass, fail or partial, and one line of evidence
- the failures, with exact reproduction steps
- the cost of the model runs

The summary and the fixes, if any, are tracked in `EVALUATION.md` under a stress-test section.
