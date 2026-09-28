# Stage 1, follow-up: pre-registration

Written 2026-09-28, after Stage 1 and before either run below. Stage 1's own rules
([`PREREG.md`](PREREG.md)) are not changed.

## Run 1: the `/mimi-close` scope fix (sqlite-utils, arm D only)

Stage 1 found `/mimi-close` dropping person-stated facts as "about your downstream service" (R1 Lambda
`/tmp`, R4 semicolon CSVs). Commit `3bdb281` says scope is never a reason to drop.

- A fresh D arm is built by Adopt. It runs the same 5 sessions, then the same 8 recall questions × 3 and
  2 continuity questions × 5. The protocol, model and judges are unchanged. Arms A, N and M are not
  re-run: their memory does not depend on D, so their Stage 1 answers stand.
- **The fix works** if R1 and R4 each score ≥ 0.67, the mean of both judges.
- **No regression** if no other sqlite-utils question falls more than 0.25 below its Stage 1 D score.
  With 3 runs per question, one missed key point in one run moves a score by about 0.17.
- If the fix works, the corrected sqlite-utils D numbers replace the Stage 1 ones in the README, with
  both shown.

## Run 2: more continuity (F2b)

Stage 1's continuity result rests on 4 questions, and mimi's lower bound over built-in auto-memory was
+0.02. F2b adds 4 new unfinished threads per repo (8 questions):

| Thread | What is left unfinished |
|---|---|
| T3 | A plan changed mid-session: a named person reversed it, and the new plan and its reason were stated |
| T4 | Experiment results: what helped, what did not, and the next diagnostic step |
| T5 | Review feedback: one item done, one left to the user, one skipped with a reason |
| T6 | A blocked task: a ticket, where a secret will come from, and a rule about it |

- All four arms (A, N, D with the fixed close, M) start fresh in new copies of each repo and run T3–T6 in
  order. There are 8 resume questions, each run 5 times from the same saved state (40 answers per arm).
  The protocol is otherwise as in Stage 1.

### Decision rules

Differences are paired by question and run, with a 95% bootstrap interval over questions.

1. **Primary, D vs N on F2b:**
   - mimi *beats auto-memory on continuity* if D − N ≥ 0.10 with an interval excluding 0.
   - If |D − N| < 0.10, it is *a tie on continuity*.
   - If N − D ≥ 0.10 with an interval excluding 0, *auto-memory wins*.
2. **Secondary, D vs M on F2b:** the same thresholds.
3. **Pooled:** D − N over all 12 continuity questions (Stage 1 F2 plus F2b) is reported alongside, not used
   for the decision.
4. The README states the primary result as it comes out, including a tie or a loss.

### Validity checks

- Every write turn finished without an error. A 40-turn cap is flagged as in Stage 1.
- N wrote at least one auto-memory file. M's worker queue was empty before the snapshot.
- A thread whose first turn asked for an edit (T5) has that edit in every arm's working tree. If it does
  not, that arm's point (a) is noted.
