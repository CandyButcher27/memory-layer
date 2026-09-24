<!-- memory-layer:start -->
## Memory

Check this section before grepping the repo. Current state loads automatically:

@STATE.md

### Where to look
- Something broke, or a symptom looks familiar → `ISSUES.md` (search the exact error text)
- About to change an existing choice (library, schema, provider, architecture) → `decisions.md`
- Touching an external system (API, database, deploy, credentials) → `memory/external.md` — contains: Jenkins AIX test machines; Internal build farm: /tmp is noexec
- Embedding Node.js, several Environments per isolate/thread, C++ standard, platform/inspector ownership flags → `memory/embedding.md` — contains: Range-for over queue.Lock().PopAll() deadlocks when built as C++23; Second Environment aborts because a per-isolate template was set per Environment; Process-wide statics break when two Environments are alive; FreeEnvironment() blocks JavaScript for sibling Environments on the same isolate; Features missing when the embedder owns the V8 platform or inspector

Every file in `memory/` gets one line above saying when to read it. A file with no line is never read. `index` appends each file's `##` headings to its line, so a task can match a trap by name.

### What to write, and where
- Bug fixed → append to `ISSUES.md`: exact symptom text, cause, fix commit, test.
- Choice someone could argue again → append to `decisions.md`: why, what was rejected, what would reverse it.
- Fact the code cannot tell you → `memory/<topic>.md`: external-system quirks, measured numbers with date and sample size, why something non-obvious exists, environment traps. Give each trap its own `##` heading, named the way a task would describe it (error text, library, table, command). Keep its `Last verified:` date current. Then run `python "$HOME/w/pub/ml/memlayer.py" index .`
- End of a work session → overwrite `STATE.md`. Finished work leaves it.
- Code change alone → nothing. Git has it.

Before writing any line: could someone learn this in under a minute from the code or a command? If yes, do not write it. Every fact needs something checkable behind it: a commit, an issue ID, a command, a date. A wrong line gets fixed or deleted, never a correct one added beside it. Split `memory/` by external boundary or subsystem, not by code folder, and only after a real miss.

Find rot: `python "$HOME/w/pub/ml/memlayer.py" check .`
<!-- memory-layer:end -->
