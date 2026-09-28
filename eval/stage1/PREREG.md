# Stage 1: pre-registration

Written 2026-09-28, before any Stage 1 run. Nothing in this file changes after the first result arrives.
A change would mean a new stage, not a revision of this one.

## Question

Does mimi keep its advantage when:
- (a) facts come up in passing inside realistic multi-turn sessions, not announced one per session
- (b) the task is continuing unfinished work, where automatic capture should do well

And does it add anything over Claude Code's built-in auto-memory?

## Arms

| Arm | Memory | Notes |
|---|---|---|
| A | None | Auto-memory off. Control |
| N | Claude Code built-in auto-memory | Default Claude Code behaviour, nothing installed |
| D | mimi | Built by Adopt (Opus). Each work session ends with a `/mimi-close` turn, the documented workflow. Auto-memory off |
| M | claude-mem 13.28.x | `npx claude-mem install --provider claude`, default settings. Auto-memory off |

Each arm runs with its own `HOME`, behind its own logging proxy. claude-mem's worker is counted from its
debug log. Task model: Sonnet. Judges: Sonnet and Opus.

## Repositories

- rust-lang/cargo at `694054f34bcb04025b16d0eaf075038c0e58a15d`: large, Rust, detailed commits.
- simonw/sqlite-utils at `6bc1d33d583c54bd69fbdd2071117e2d38c354a1`: small Python app, 1,203 commits,
  terse commit messages.

## Task families

**F1: stated facts in realistic sessions.** Per repo, 3 multi-turn work sessions (2–3 turns each). Each
turn asks a real question about the code. 8 facts are mentioned in passing inside those turns, next to
noise the questions never ask about:
- an external constraint
- a trap
- a person who owns something
- a measurement
- a decision and its reason
- a deadline
- a review rule
- an infrastructure detail

One fact is corrected in a later session. There are 8 recall questions per repo, 3 runs each.

**F2: continuity.** Per repo, 2 work threads left unfinished, each in its own session:
- **T1, a feature:** the user gives a 3-step plan, the agent does step 1, and the user mentions a dead end
  and a constraint.
- **T2, an investigation:** the user states two ruled-out hypotheses and the next step.

A fresh session then asks to resume each thread. 2 questions per repo, 5 runs each.

Every eval run starts from the same saved state (repo copy, `HOME`, claude-mem database), so no run sees
another run's session. The eval prompt suffix is neutral: it does not say "answer from this repository".

## Measures

- Accuracy: key points hit, as a fraction, the mean of both judges. Wrong claims per answer.
- Per answer: context tokens, cost, tool calls, time.
- Write phase: task-model cost, `/mimi-close` cost (counted inside D), and background model tokens.

## Decision rules

Differences are paired by question and run. The 95% interval is a bootstrap over questions.

1. **F1:**
   - mimi *keeps its advantage* if D − M ≥ 0.15 and D − N ≥ 0.15, each with an interval excluding 0.
   - If |D − M| < 0.10, the F1 result is *a tie*.
2. **F2:**
   - claude-mem *wins continuity* if M − D ≥ 0.15 with an interval excluding 0.
   - mimi *wins continuity* if D − M ≥ 0.15 with an interval excluding 0.
   - Otherwise it is *no difference shown*. F2 has only 20 answers per arm, so only large effects can show.
3. **Built-in default:** if N ≥ D − 0.10 in both families, mimi has not shown value over Claude Code's
   default, and the README must say so.
4. **Cost:** report it; no threshold. If mimi wins accuracy, cost is secondary. If it ties, cost decides.

## Validity checks (a failing check marks that arm invalid for that repo)

- Every write-session turn finished without an error.
- M: the claude-mem worker queue was empty and every write session produced at least one observation
  before the snapshot.
- N: at least one auto-memory file exists after the write phase. If none does, N is reported as
  equivalent to A, not dropped.
- F2 T1: step 1 exists in the working tree after the T1 session. If an arm did not do step 1, that
  arm's key point 1 is noted, not re-scored.

## Known limits, stated in advance

- I wrote the facts and the sessions, so some home advantage remains. The facts are now said in passing,
  and F2 is a task that favours automatic capture.
- Sessions are headless. The judges are the same model family as the task model.
