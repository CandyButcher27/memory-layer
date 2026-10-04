<p align="center">
  <img src="banner/memory-layer-banner.png" alt="mimi" width="420">
</p>

<h3 align="center">Project memory for coding agents that keeps only what your code can't tell them.</h3>

<p align="center">
  Claude Code · Codex · OpenCode · Gemini CLI · Antigravity · Cursor · any agent that reads <code>SKILL.md</code>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11%2B-blue" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/dependencies-none-brightgreen" alt="Dependencies: none">
  <img src="https://img.shields.io/badge/storage-markdown%20in%20your%20repo-lightgrey" alt="Storage: markdown in your repo">
  <img src="https://img.shields.io/badge/license-MIT-yellow" alt="License: MIT">
</p>

---

Coding agents start every session knowing nothing about your project. Most memory tools record
everything the agent does and replay summaries of it. mimi does the opposite: it keeps a small, reviewed
memory in one `mimi/` folder in your project and stores only what is not in the code. That means bugs
and their causes, decisions and the options you rejected, quirks of external systems, measured numbers,
and what people told the agent.

No server, database, hooks or background process. Four skills and one standard-library Python script.

## Install

Paste this into your coding agent:

```text
Install mimi for me by following the "Steps for an agent doing the install" section of
https://github.com/CandyButcher27/memory-layer/blob/main/docs/INSTALL.md
```

Or run it yourself (needs Node.js and Python 3.11+):

```bash
npx skills add CandyButcher27/memory-layer -g --skill '*'
```

Manual install, per-agent folders, and slash commands for OpenCode and Gemini CLI:
**[docs/INSTALL.md](docs/INSTALL.md)**.

## Use

| Command | When | What it does |
|---|---|---|
| `/mimi-start` | Once per project | Creates `mimi/` and loads it from `CLAUDE.md`, `AGENTS.md` or `GEMINI.md`. On an existing project it adopts your old notes, git history and issues, keeping only what passes the one-minute test |
| `/mimi-close` | End of each work session | Files what the session learned: bugs to `ISSUES.md`, choices to `decisions.md`, external facts to `memory/`, and rewrites `STATE.md` with a handoff for next time |
| `/mimi-logging` | Any time | Reports what mimi costs and saves in this project |

Nothing to run at the start of a session: the memory loads by itself. In Codex, type `$mimi-start`
instead of `/mimi-start`. In any agent you can also say "run the mimi-start skill".

**The one-minute test:** could someone learn this in under a minute from the code or a command? If yes,
mimi does not write it down.

How the folder, index and script work: **[docs/HOW_IT_WORKS.md](docs/HOW_IT_WORKS.md)**.

## Results

Against Claude Code's built-in auto-memory and five other memory tools, with the questions and pass criteria
committed before the run (Sonnet 5.5, 2026-10-04):

| | No memory | Built-in auto-memory | claude-mem | Best other tool | mimi |
|---|---|---|---|---|---|
| Facts and unfinished work from earlier sessions (10 questions, 7 tools) | — | 0.11 | 0.47 | recall 0.56 | **0.94** |
| Resuming unfinished work, on sqlite-utils and cargo (8 questions) | 0.21 | 0.17 | 0.25 | — | **0.89** |
| 12 sessions: facts stated, corrected, found in files, and work in progress (18 questions) | 0.21 | 0.44 | 0.40 | recall 0.61 | **0.94** |
| The same 12 sessions, but `/mimi-close` never run | | | | | 0.43 |
| Cost per answer | $0.05 | $0.03–0.05 | $0.06 | $0.04–0.05 | **$0.04** |

An earlier round on Sonnet 5 (Stage 1) gave the same order with a stronger auto-memory: on facts mentioned in
passing, 0.83 for mimi against 0.51 for auto-memory and 0.15 for claude-mem.

Where this is thin:
- **mimi only works if you close the session.** Without `/mimi-close`, it tied built-in auto-memory.
- Tools that record everything automatically kept more of what the agent read in files (0.88 against 0.75).
- On Sonnet 5.5, auto-memory rarely chose to save anything, which makes its scores here low.
- Each `/mimi-close` costs about $0.20–0.50.
- mimi does not beat plain `git log` at finding past incidents in repositories whose commit messages
  already explain them.

How the evaluation works: **[eval/README.md](eval/README.md)**. Every number, decision rule and limitation:
**[eval/bench/RESULTS.md](eval/bench/RESULTS.md)** and **[docs/EVALUATION.md](docs/EVALUATION.md)**.
Stress tests: **[docs/STRESS_TESTS.md](docs/STRESS_TESTS.md)**.

## Repository layout

```
skills/
  mimi/             the core skill: SKILL.md, memlayer.py, templates/
  mimi-start/       /mimi-start
  mimi-close/       /mimi-close
  mimi-logging/     /mimi-logging
commands/           slash-command files for OpenCode and Gemini CLI
docs/               INSTALL, HOW_IT_WORKS, EVALUATION, STRESS_TESTS
banner/             the logo
eval/               how it is evaluated, harnesses, task files, verdicts and results
AGENTS.md           what mimi does, written for agents
```

## License

[MIT](LICENSE)
