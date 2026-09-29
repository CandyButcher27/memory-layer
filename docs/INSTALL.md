# Installing mimi

mimi is four [Agent Skills](https://agentskills.io) (`mimi`, `mimi-start`, `mimi-close`, `mimi-logging`)
and one standard-library Python script. You need Python 3.11+ on `PATH` (`python` or `python3`). Install
the skills once, at user level, and they work in every project.

The four skill folders must sit side by side in the same skills folder. `mimi-start` finds the script at
`../mimi/memlayer.py`, so installing one without the others breaks it.

- [Let your agent install it](#let-your-agent-install-it)
- [One command](#one-command)
- [By hand](#by-hand)
- [Slash commands in each agent](#slash-commands-in-each-agent)
- [Update and uninstall](#update-and-uninstall)
- [Steps for an agent doing the install](#steps-for-an-agent-doing-the-install)

## Let your agent install it

Paste this into Claude Code, Codex, OpenCode, Gemini CLI, Cursor, Antigravity or any other coding agent:

```text
Install mimi for me by following the "Steps for an agent doing the install" section of
https://github.com/CandyButcher27/memory-layer/blob/main/docs/INSTALL.md
```

## One command

With Node.js, the [`skills`](https://github.com/vercel-labs/skills) CLI installs all four skills into
every agent you choose:

```bash
npx skills add CandyButcher27/memory-layer -g --skill '*'
```

It asks which agents to install into. To skip the questions, name the agents:

```bash
npx skills add CandyButcher27/memory-layer -g --skill '*' -a claude-code -a codex -a opencode -a gemini-cli -a cursor -a antigravity -y
```

`-g` installs at user level, for every project. Leave it out to install into the current project only.
If symlinks fail (common on Windows without Developer Mode), add `--copy`.

Then add the slash commands for OpenCode or Gemini CLI if you use them (see
[below](#slash-commands-in-each-agent)), and check the script:

```bash
python ~/.agents/skills/mimi/memlayer.py selftest    # prints SELFTEST_OK
```

## By hand

```bash
git clone https://github.com/CandyButcher27/memory-layer
cd memory-layer
D=~/.claude/skills                  # your agent's folder from the table below
mkdir -p "$D"
cp -r skills/mimi skills/mimi-start skills/mimi-close skills/mimi-logging "$D"/
python "$D/mimi/memlayer.py" selftest   # prints SELFTEST_OK
```

On Windows PowerShell, use `$D = "$HOME\.claude\skills"` and
`Copy-Item -Recurse skills\mimi, skills\mimi-start, skills\mimi-close, skills\mimi-logging $D`.

| Agent | User-level skills folder `D` | Memory loads from |
|---|---|---|
| Claude Code | `~/.claude/skills` | `CLAUDE.md` |
| Codex CLI | `~/.agents/skills` | `AGENTS.md` |
| OpenCode | `~/.config/opencode/skills` (also reads `~/.claude/skills` and `~/.agents/skills`) | `AGENTS.md`, or `CLAUDE.md` if there is none |
| Gemini CLI | `~/.gemini/skills` or `~/.agents/skills` | `GEMINI.md` |
| Antigravity | `~/.gemini/config/skills` | `GEMINI.md` or `AGENTS.md` |
| Cursor | `~/.cursor/skills` | `AGENTS.md` |
| GitHub Copilot | `~/.copilot/skills` | `AGENTS.md` |
| Windsurf | `~/.codeium/windsurf/skills` | `AGENTS.md` |

Copying into both `~/.claude/skills` and `~/.agents/skills` covers Claude Code, Codex, OpenCode and Gemini
CLI at once. For any other agent, `npx skills add CandyButcher27/memory-layer --list` and its agent list
show the right folder.

mimi runs on whatever model the agent uses. A model such as DeepSeek or a local model has no skills
folder of its own: install mimi into the agent you run it in.

## Slash commands in each agent

| Agent | Start | Close | Report |
|---|---|---|---|
| Claude Code | `/mimi-start` | `/mimi-close` | `/mimi-logging` |
| Cursor | `/mimi-start` | `/mimi-close` | `/mimi-logging` |
| Antigravity | `/mimi-start` | `/mimi-close` | `/mimi-logging` |
| Codex CLI | `$mimi-start` | `$mimi-close` | `$mimi-logging` |
| OpenCode | `/mimi-start` after adding the command files below | | |
| Gemini CLI | `/mimi-start` after adding the command files below | | |
| Any other agent | "run the mimi-start skill" | "run the mimi-close skill" | "run the mimi-logging skill" |

OpenCode and Gemini CLI load skills only when the model decides to. The repository ships small command
files that turn each skill into a slash command. From the cloned repository:

```bash
mkdir -p ~/.config/opencode/commands && cp commands/opencode/*.md ~/.config/opencode/commands/   # OpenCode
mkdir -p ~/.gemini/commands && cp commands/gemini/*.toml ~/.gemini/commands/                     # Gemini CLI
```

Restart the agent after installing so it picks up the new skills and commands.

## Update and uninstall

Installed with `npx skills`:

```bash
npx skills update -g
npx skills remove -g mimi mimi-start mimi-close mimi-logging
```

Installed by hand: `git pull` in the clone and copy the four folders again, or delete them to uninstall.
Uninstalling never touches a project's `mimi/` folder. To remove mimi from a project, delete `mimi/` and
the block between `<!-- memory-layer:start -->` and `<!-- memory-layer:end -->` in its instruction files.

## Steps for an agent doing the install

You are installing mimi for the user. Do these steps in order and report the result of each.

1. Find out which coding agents the user uses. Ask if it is not clear. Include the one you are running in.
2. Check that Python 3.11+ runs as `python` or `python3`. If neither works, stop and tell the user.
3. If `npx` is available, run:
   `npx skills add CandyButcher27/memory-layer -g --skill '*' -a <agent> [-a <agent> ...] -y`
   using the agent ids `claude-code`, `codex`, `opencode`, `gemini-cli`, `cursor`, `antigravity`,
   `github-copilot`, `windsurf`. If it fails on symlinks, run it again with `--copy`.
   Without `npx`, clone `https://github.com/CandyButcher27/memory-layer` to a temporary folder and copy
   the four folders `skills/mimi`, `skills/mimi-start`, `skills/mimi-close` and `skills/mimi-logging`
   into each agent's user-level skills folder from the table in [By hand](#by-hand). Keep the four
   folders side by side.
4. For OpenCode, copy `commands/opencode/*.md` into `~/.config/opencode/commands/`. For Gemini CLI, copy
   `commands/gemini/*.toml` into `~/.gemini/commands/`. Clone the repository for this if step 3 did not.
5. Run `python <skills folder>/mimi/memlayer.py selftest` for one installed copy. It must print
   `SELFTEST_OK`.
6. Delete any temporary clone. Do not create `mimi/` in any project: that is what `mimi-start` does.
7. Tell the user where the skills went, how to call them in their agent (table in
   [Slash commands](#slash-commands-in-each-agent)), and that they should restart the agent, then run
   `mimi-start` once in each project.
