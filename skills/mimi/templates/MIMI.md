## Memory (mimi)

Check this before grepping the repo. Everything mimi keeps is in `mimi/`, and the current state loads automatically:

@STATE.md

### Where to look
- Something broke, or a symptom looks familiar → `mimi/ISSUES.md` (search the exact error text)
- About to change an existing choice (library, schema, provider, architecture) → `mimi/decisions.md`
- Touching an external system (API, database, deploy, credentials) → `mimi/memory/external.md`

Every file in `mimi/memory/` gets one line above saying when to read it. A file with no line is never read. `index` appends each file's `##` headings to its line, so a task can match a trap by name, and marks a file that holds nothing yet as `— empty`: skip those.

Memory holds only what someone wrote down. When it has nothing on the question, that is not an answer: search `git log --grep`, the issue tracker and the code before concluding.

### What to write, and where
- Bug fixed → append to `mimi/ISSUES.md`: exact symptom text, cause, fix commit, test.
- Choice someone could argue again → append to `mimi/decisions.md`: why, what was rejected, what would reverse it.
- Fact the code cannot tell you → `mimi/memory/<topic>.md`: external-system quirks, measured numbers with date and sample size, why something non-obvious exists, environment traps. Give each trap its own `##` heading, named the way a task would describe it (error text, library, table, command). Keep one `Last verified:` line per file, dated when its facts were last checked.
- End of a work session → overwrite `mimi/STATE.md` (or run the `mimi-close` skill). Finished work leaves it.
- Code change alone → nothing. Git has it.
- After any memory edit: run `python "{memlayer}" index .`, then `python "{memlayer}" check .` and fix what it prints until it says clean.

Before writing any line: could someone learn this in under a minute from the code or a command? If yes, do not write it. Ask it of each fact on its own, not of the message the fact came in: a number, date, measurement, deadline, decision or constraint that a person stated is never in the code, even when the code touches the same topic, and a fact about the user's own systems, team or downstream use of this code is kept even when this repository never touches it. Every fact needs something checkable behind it: a commit, an issue ID, a command, a date. A wrong line gets fixed or deleted, never a correct one added beside it. Split `mimi/memory/` by external boundary or subsystem, not by code folder, and only after a real miss.

`mimi/` is ignored by git through `mimi/.gitignore`, so this memory stays on this machine. Delete that file to share it through git.

Find rot: `python "{memlayer}" check .`
