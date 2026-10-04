# Rivals R7 re-run: pre-registration

Written 2026-10-04, before any job of this run. Nothing in this file changes after the first result arrives.

## Question

Does the `index` fix for `decisions.md` (commit `4b4ab9c`, PR #2) recover rivals question R7, without losing
anything else?

In the bench's rivals track, R7 ("Can I use `sqlite-utils insert --replace` for the production ingest?") fell from
1.00 in Stage 1 to 0.33. The rule was stored under a `decisions.md` heading, whose index line listed nothing, and the
agent stopped at a memory file whose headings matched. PREREG-2 Run 1 failed on that drop.

## Design

- **Track `rivals-fix`:** the rivals track's sqlite-utils sessions (S1–S5) and its 10 questions, on the same commit
  (`6bc1d33`), for arm D only.
- **mimi under test:** `skills/` at `e13ef3e`. The only change from the rivals track's v0.1.0 is PR #2: the `index`
  fix, the `AGENTS.md` opt-out marker (sqlite-utils has no `AGENTS.md`), and the bench's transcript cleanup.
- **Model pinned:** `claude-sonnet-5-5` by full ID, the model the rivals track ran on. The judge stays `sonnet`, as in
  every bench track.
- **Runs:** 3 per question, as in the rivals track. Everything else follows PREREG-3.
- **Baseline:** the rivals track's arm D (`results/rivals/`), same sessions, model and judge.

## Decision rules

1. **R7 recovered** if it scores ≥ 0.67 over its 3 runs.
2. **Scope fix still holds** if R1 and R4 each score ≥ 0.67.
3. **No regression** if no other question scores more than 0.25 below the rivals track's D.

If all three hold, PREREG-2 Run 1 passes on the fixed version. The results say so either way, with a loss reported
as plainly as a win.

## Known limits, stated in advance

- 3 runs of one question cannot show a small effect. This tests whether the miss was the index line.
- The author of the fix also wrote the question.
- About $4–5 API-equivalent: Adopt build, 5 write sessions with `/mimi-close`, 30 answers.
