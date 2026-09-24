# Public-repo evaluation protocol

One agent per repo, each following exactly these steps, so results compare across repos. Everything
model-driven runs on a GitHub Codespace, never on the local Windows machine, which runs out of memory.

- **Local output folder:** `eval/public/<repo>/` in this repository
  (`<repo>` like `django`)
- **Bundle:** a local `pubbundle.tgz`

It unpacks to `pub/`:

| Path | Contents |
|---|---|
| `pub/ml/` | The memory layer under test: `SKILL.md`, `memlayer.py`, `templates/`, `commands/` |
| `pub/harness/SKILL.md` | The current memory setup's skill (baseline arm B) |
| `pub/run.py` | Runner and dual judge (`run`, `session`, `judge2`, `report`, `report2`, env `ARMS`/`TASKS`/`RESULTS`/`MODEL`) |
| `pub/hygiene.py` | Memory-write analysis |
| `pub/setup.sh` | Claude auth check |
| `pub/example_tasks/` | Task-file formats: `sessions.json`, `recall.json` |

## 0. Codespace

Run these from the Bash tool (Git Bash). Call it `CS`.

```bash
CS=$(gh codespace create -R CandyButcher27/host-repo -b main -m standardLinux32gb --display-name ml-<repo> --idle-timeout 240m | tail -1)
gh codespace cp -c "$CS" "<bundle path>" remote:/tmp/pub.tgz
gh codespace ssh -c "$CS" -- 'mkdir -p ~/w && tar xzf /tmp/pub.tgz -C ~/w && sudo npm install -g @anthropic-ai/claude-code >/dev/null 2>&1; python3 -c "import json,shlex; v=json.load(open(\"/workspaces/.codespaces/shared/user-secrets-envs.json\"))[\"CLAUDE_CODE_OAUTH_TOKEN\"].strip(); open(\"/home/codespace/w/env.sh\",\"w\").write(\"export CLAUDE_CODE_OAUTH_TOKEN=\"+shlex.quote(v)+\"\n\")" && chmod 600 ~/w/env.sh && . ~/w/env.sh && cd ~/w/pub && bash setup.sh'
```

It must print `auth: ok`.

- **Long jobs:** start them detached (`nohup bash -c "..." > log 2>&1 < /dev/null &`, inside a
  subshell) and poll with foreground until-loops. Each Bash call must stay under 9 minutes.
- **Environment:** every model command sources `~/w/env.sh` first.
- **Parallelism:** run at most 3 `claude` processes at a time. Four other agents share the same Claude
  account.
- **Usage limit:** if a run's result reads `You've hit your session limit`, stop launching new runs.
  Keep what is finished, and report partial results.
- **Cleanup:** delete the Codespace at the end, even after a failure:
  `gh codespace delete -c "$CS" --force`.

## 1. Source

```bash
git clone https://github.com/<org>/<repo> ~/w/src   # nodejs/node: add --filter=blob:none
```

- Record `git rev-parse HEAD`, the commit count, and the file count.
- Make a base copy `~/w/base`, then remove agent-instruction files so every arm starts equal:
  `CLAUDE.md`, `AGENTS.md`, `.claude/`, `.cursor/`, `.cursorrules`, `.github/copilot-instructions.md`,
  `GEMINI.md`. Commit the removal as `eval: strip agent instructions`.

## 2. Tasks, written before any memory exists

You, the agent, write the tasks by reading raw git on the Codespace (`git log`, `git show`). No arm's
memory exists yet, so the answer keys cannot come from it.

**`tasks.json`:** 10 retrieval tasks, in the same schema as `{id, kind, source, task, gold}`.

| Kind | Count | What it is |
|---|---|---|
| recurring bug | 4 | Give the symptom (exact error or behaviour from the commit message). The answer is the cause and the fix |
| decision | 3 | "Should we do X?" where history shows X was rejected or reverted, with the reason |
| platform or external quirk | 2 | OS, compiler, CI or third-party behaviour the project works around |
| code control | 1 | Answerable from current code alone |

- Use commits from the last 3 years with explanatory bodies.
- Phrase each task the way a colleague would, without naming the commit.
- `gold` holds 2–3 key points, taken only from the commit message or diff.

**`sessions.json`:** 5 write sessions, in the format of `example_tasks/sessions.json`. Each one
states a fact only a person could know and asks a small read-only question about the repo.
- S1: an external or CI fact with two parts
- S2: a maintainer decision with its reason
- S3: a measurement with a number, date and sample size
- S4: a trap
- S5: a correction to part of S1

**`recall.json`:** 5 recall questions, one per session fact, in the format of
`example_tasks/recall.json`. The corrected fact's key requires the new value and rejects the old one.

## 3. Arms

All arms are copies of `~/w/base`, in `~/w/arms/<letter>`.

| Arm | Contents | Built by |
|---|---|---|
| A | No memory | Nothing |
| B | Current memory setup | `claude -p --model opus` with this prompt: "Follow the skill at /home/codespace/w/pub/harness/SKILL.md to do a fresh scaffold on this project (the current directory). No user is available: do not ask questions, skip step 6 (installing skills and agents) because there is no template source on this machine, and finish with a short report." Allowed tools: `Read Write Edit Grep Glob Bash`. Disallowed: `Agent Workflow WebFetch WebSearch` |
| D | This memory layer | `claude -p --model opus` with this prompt: "Follow the skill at /home/codespace/w/pub/ml/SKILL.md in Adopt mode on this project (the current directory). Its script is /home/codespace/w/pub/ml/memlayer.py. No user is available: a claim with nothing checkable behind it is dropped, not asked about. Do not delete any file. Finish when `python3 /home/codespace/w/pub/ml/memlayer.py check .` prints \"memory layer clean\", then print a short report." Same tools |

After building each arm, record:
- cost and turns (from the `result` event, using `--output-format stream-json --verbose`)
- memory line counts
- `memlayer.py check` output for D
- auto-loaded bytes (`CLAUDE.md` + `STATE.md`)

## 4. Runs

The task model is **Sonnet**. Opus hit the ceiling on retrieval in an earlier experiment, so it could
not separate the setups.

```bash
cd ~/w/pub
MODEL=sonnet ARMS=ABD python3 run.py run ~/w/arms all 2 3
mkdir -p ~/w/wr ~/w/snap && cp -r ~/w/arms/B ~/w/wr/E && cp -r ~/w/arms/D ~/w/wr/F && cp -r ~/w/wr/E ~/w/snap/E && cp -r ~/w/wr/F ~/w/snap/F
MODEL=sonnet ARMS=EF TASKS=sessions.json RESULTS=results_sessions python3 run.py session ~/w/wr
MODEL=sonnet ARMS=EF TASKS=recall.json RESULTS=results_recall python3 run.py run ~/w/wr all 3 3
python3 hygiene.py ~/w/wr ~/w/snap > hygiene_out.txt
ARMS=ABD python3 run.py judge2 ~/w/arms > judge2_main.txt
ARMS=EF TASKS=recall.json RESULTS=results_recall python3 run.py judge2 ~/w/wr > judge2_recall.txt
ARMS=ABD python3 run.py report > report_main.txt
ARMS=EF TASKS=recall.json RESULTS=results_recall python3 run.py report > report_recall.txt
```

`tasks.json`, `sessions.json` and `recall.json` go in `~/w/pub/`. Smoke-test first: one task on all
three arms, then `judge2` on it. Check both verdicts parse before launching the full run.

## 5. Output

Copy these back into the local output folder:
- `tasks.json`, `sessions.json`, `recall.json`
- the report, `judge2` and hygiene files
- a build-stats file
- the `results*/` folders, including the raw `.jsonl`

Then write `RESULTS.md` covering:
- **Repo:** URL, pinned SHA, commits, files, language.
- **Arm builds:** cost, turns, lines, auto-loaded bytes, `check` result.
- **Retrieval:** per arm (both judges' accuracy, disagreement, wrong claims, tool and search calls,
  tokens, cost), plus per task.
- **Write and recall:** lines written per arm, recall accuracy, cost per answer, whether the S5
  correction was edited in place.
- **Transcript check:** on the tasks where the arms differ, did the memory arms open their memory
  files, and did it help?
- Anything that broke, total spend, and whether the Codespace was deleted.

**Budget:** stop at $40 of total model spend for the repo.
