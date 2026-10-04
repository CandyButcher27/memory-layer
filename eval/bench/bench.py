import fcntl
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

CODE = Path(__file__).resolve().parent
MIMI_SRC = CODE.parent.parent
ROOT = Path(os.environ.get("BENCH_ROOT", Path.home() / "bench"))
PLAN = json.loads((CODE / "plan.json").read_text(encoding="utf-8"))
MODEL = PLAN["model"]
ALL_ARMS = ("A", "N", "D", "D0", "M", "L", "G", "R", "K", "S")
AUTO_MEMORY = {"N"}
MIMI = {"D", "D0"}
CLOSE = {"D": "/mimi-close"}
LIMIT = re.compile(r"(?i)usage limit|hit your limit|limit reached|rate[ _-]?limit|resets? (at|in)|overloaded|\b429\b|\b529\b")
AUTH = re.compile(r"(?i)failed to authenticate|authentication_error|invalid api key|oauth token|not logged in|/login")
EVAL_SUFFIX = (
    "\n\nDo not modify any file, and do not connect to the network."
    " Keep the answer under 200 words and say what you relied on."
)
ADOPT = (
    "Follow the skill at {skill} in Adopt mode on this project (the current directory). Its script is {ml}."
    " No user is available: a claim with nothing checkable behind it is dropped, not asked about. Do not delete"
    ' any file. Finish when `python3 {ml} check .` prints "memory layer clean", then print a short report.'
)
NO_TOOLS = "Agent Task WebFetch WebSearch"
SKIP_HOME = ["--exclude=/.npm/", "--exclude=/.cache/", "--exclude=/.bun/", "--exclude=/.rustup/",
             "--exclude=/.cargo/", "--exclude=node_modules/", "--exclude=logs/", "--exclude=*.log",
             "--exclude=/.claude/.credentials.json"]
JUDGE = """You are grading an answer to a question about a software repository. You have no tools; do not try to use any.

Question:
{task}

Key points a correct answer contains:
{points}

Answer to grade:
<<<
{answer}
>>>

The answer comes from an agent working in the real repository, so it will contain extra details the key points
do not mention (branch names, other open issues, file paths). Extra details are expected and are not evidence
that the answer is wrong. Judge each key point on its own.

For each key point, quote the sentence from the answer that states it (paraphrase counts), or write "none".
Then count claims that directly contradict a key point. Unverifiable extra details are not contradictions.
End with this JSON on its own last line:
{{"hits": [true/false for each key point, in order], "wrong": <int>, "note": "<one short sentence>"}}"""


OVERAGE: dict = {}


class Pause(Exception):
    pass


class Fail(Exception):
    pass


def log(**kw) -> None:
    kw["ts"] = time.time()
    with (ROOT / "jobs.log").open("a", encoding="utf-8") as f:
        f.write(json.dumps(kw) + "\n")
    print(json.dumps(kw), flush=True)


def track(t: str) -> dict:
    cfg = PLAN["tracks"][t]
    load = lambda k: json.loads((CODE / cfg[k]).read_text(encoding="utf-8"))
    return {**cfg, "S": load("sessions"), "Q": load("eval"), "dir": ROOT / t}


def reps(cfg: dict, qid: str) -> int:
    return cfg["reps"].get(qid[0], cfg["reps"]["default"])


def token() -> str:
    p = ROOT / ".oauth_token"
    if not p.exists():
        raise Pause(f"missing {p}: run `claude setup-token` and save the token there")
    return p.read_text(encoding="utf-8").strip()


def port(arm: str) -> int:
    return 8900 + ALL_ARMS.index(arm)


def env(t: str, arm: str) -> dict:
    d = ROOT / t
    e = {k: v for k, v in os.environ.items() if not k.startswith("ANTHROPIC_")}
    # Windows shims on the WSL PATH (bun, npm) start tools on the Windows side, where they silently fail
    path = [p for p in e["PATH"].split(":") if not p.startswith("/mnt/")]
    e.update(PATH=":".join([str(Path.home() / ".bun/bin"), *path]), HOME=str(d / "home" / arm), WR=str(d / "wr" / arm), ARM=arm, MIMI_SRC=str(MIMI_SRC), CODE=str(CODE),
             CLAUDE_CODE_OAUTH_TOKEN=token(), DISABLE_AUTOUPDATER="1", CPORT=str(37700 + ALL_ARMS.index(arm)))
    if os.environ.get("BENCH_PROXY", "1") == "1":
        e["ANTHROPIC_BASE_URL"] = f"http://127.0.0.1:{port(arm)}"
    if arm == "L":
        # claude-mem-lite 6.21 and its better-sqlite3 13 need Node >= 22; WSL's default node is 20
        e["PATH"] = f"{Path.home()}/.nvm/versions/node/v22.23.3/bin:{e['PATH']}"
    if arm not in AUTO_MEMORY:
        e["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
    if arm == "S":
        key = ROOT / ".supermemory_key"
        if not key.exists():
            raise Pause(f"missing {key}: create a Supermemory API key and save it there")
        e["SUPERMEMORY_CC_API_KEY"] = key.read_text(encoding="utf-8").strip()
        e["TAG"] = f"mimibench-{t}-{arm}"
    return e


def sh(*cmd, **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def arm_do(t: str, arm: str, action: str) -> str:
    r = sh("bash", str(CODE / "arms.sh"), action, env=env(t, arm), timeout=1800)
    if r.returncode:
        raise Fail(f"arms.sh {action} {arm}: {(r.stdout + r.stderr)[-800:]}")
    return r.stdout


def rsync(src: Path, dst: Path, *extra: str) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    r = sh("rsync", "-a", "--delete", *extra, f"{src}/", f"{dst}/")
    if r.returncode:
        raise Fail(f"rsync {src} -> {dst}: {r.stderr[-400:]}")


def snap(t: str, arm: str, name: str, restore: bool = False) -> None:
    d = ROOT / t
    s = d / "snap" / name / arm
    pairs = ((d / "wr" / arm, s / "wr", ["--exclude=/target/"]), (d / "home" / arm, s / "home", SKIP_HOME))
    for live, saved, ex in pairs:
        rsync(*((saved, live) if restore else (live, saved)), *ex)


def claude(prompts: list[str], cwd: Path, e: dict, out: Path, disallow: str, model: str = MODEL) -> dict:
    session, results, quota = None, [], {}
    with out.open("w", encoding="utf-8") as f:
        for prompt in prompts:
            cmd = ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose", "--model", model,
                   "--max-turns", "40", "--permission-mode", "bypassPermissions", "--disallowedTools", disallow]
            if session:
                cmd += ["--resume", session]
            try:
                r = sh(*cmd, cwd=cwd, env=e, timeout=1800)
            except subprocess.TimeoutExpired:
                raise Fail(f"timeout: {prompt[:60]}")
            f.write(r.stdout)
            events = []
            for line in r.stdout.splitlines():
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
            res = next((ev for ev in reversed(events) if ev.get("type") == "result"), None)
            quota = next((ev["rate_limit_info"] for ev in reversed(events) if ev.get("type") == "rate_limit_event"), quota)
            text = (res or {}).get("result") or r.stderr[-600:]
            if not res or res.get("is_error"):
                if AUTH.search(text):
                    raise Pause(f"auth: {text[:300]}")
                if LIMIT.search(text) or not res:
                    raise Pause(f"limit or no result (killed?): {text[:300]}")
            if res.get("is_error") and res.get("subtype") != "error_max_turns":
                raise Fail(f"{res.get('subtype')}: {text[:300]}")
            results.append(res)
            session = res.get("session_id")
    if quota.get("isUsingOverage"):
        OVERAGE.update(quota)
    windows = quota.get("unifiedWindows", {})
    return {"turns": len(results), "cost": sum(r.get("total_cost_usd", 0) for r in results),
            "max_turns_hit": sum(r.get("subtype") == "error_max_turns" for r in results),
            "five_hour": windows.get("five_hour", {}).get("utilization"), "seven_day": windows.get("seven_day", {}).get("utilization")}


def halt(reason: str) -> None:
    (ROOT / "halt").write_text(reason, encoding="utf-8")
    raise Pause(f"halted: {reason}")


def background_limited(home: Path, since: float, pattern: str = r"(?i)(usage limit reached|hit your limit|rate_limit_error|You've reached your)", *more: Path) -> str:
    r = sh("find", str(home), *map(str, more), "-type", "f", "-newermt", f"@{since}", "-size", "-20M",
           "-not", "-path", "*/node_modules/*", "-not", "-path", "*/.npm/*",
           # Claude Code's flag cache holds UI strings such as "Usage limit reached"
           "-not", "-name", ".claude.json*", "-not", "-path", "*/.claude/backups/*",
           # plugin code and docs quote these errors; a self-update rewriting them is not a failure
           "-not", "-path", "*/.claude/plugins/*", "-not", "-name", "*.mjs", "-not", "-name", "*.js",
           "-not", "-name", "*.py", "-not", "-name", "*.md")
    for p in r.stdout.splitlines():
        try:
            text = Path(p).read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in re.finditer(pattern, text):
            return f"{p}: {text[max(0, m.start() - 80):m.end() + 80]}"
    return ""


def setup(t: str, arm: str) -> None:
    cfg, d = track(t), ROOT / t
    src = d / "src"
    if not (src / ".git").exists():
        r = sh("git", "clone", "-q", cfg["repo"], str(src))
        if r.returncode:
            raise Fail(r.stderr)
    sh("git", "-C", str(src), "checkout", "-q", cfg["sha"])
    wr, home = d / "wr" / arm, d / "home" / arm
    if not wr.exists():
        shutil.copytree(src, wr, symlinks=True)
    home.mkdir(parents=True, exist_ok=True)
    out = arm_do(t, arm, "install")
    (d / f"install_{arm}.txt").write_text(out, encoding="utf-8")


def build(t: str) -> None:
    d = ROOT / t
    e = env(t, "D")
    ml = Path(e["HOME"]) / ".claude/skills/mimi/memlayer.py"
    prompt = ADOPT.format(skill=ml.with_name("SKILL.md"), ml=ml)
    (d / "results").mkdir(exist_ok=True)
    try:
        m = claude([prompt], d / "wr" / "D", e, d / "results" / "build_D.jsonl", NO_TOOLS, PLAN["build_model"])
    except Fail as ex:
        if "model" not in str(ex).lower():
            raise
        log(event="deviation", track=t, note=f"Adopt build fell back to {MODEL}: {ex}"[:500])
        m = claude([prompt], d / "wr" / "D", e, d / "results" / "build_D.jsonl", NO_TOOLS)
    r = sh("python3", str(ml), "check", str(d / "wr" / "D"))
    if r.returncode:
        raise Fail(f"mimi check not clean after Adopt: {r.stdout[-600:]}")
    if "D0" in track(t)["arms"]:
        for part in ("wr", "home"):
            rsync(d / part / "D", d / part / "D0")
    log(event="build", track=t, **m)


def plant(files: list[dict], remove: bool = False) -> None:
    for f in files:
        p = Path(f["path"])
        if remove:
            p.unlink(missing_ok=True)
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(f["content"].encode(f.get("encoding", "utf-8")))


def write(t: str, arm: str, s: dict) -> None:
    d = ROOT / t
    arm_do(t, arm, "down")
    # a marker naming this session means an earlier attempt was killed mid-run: start again from its snapshot
    marker = d / "snap" / "pre" / f"{arm}.job"
    if marker.exists() and marker.read_text() == s["id"]:
        snap(t, arm, "pre", restore=True)
    else:
        snap(t, arm, "pre")
        marker.write_text(s["id"])
    plant(s.get("plant", []))
    since = time.time()
    try:
        arm_do(t, arm, "up")
        (d / "results" / "sessions").mkdir(parents=True, exist_ok=True)
        prompts = s["turns"] + ([CLOSE[arm]] if arm in CLOSE else [])
        m = claude(prompts, d / "wr" / arm, env(t, arm), d / "results" / "sessions" / f"{arm}_{s['id']}.jsonl", NO_TOOLS)
        arm_do(t, arm, "drain")
        if hit := background_limited(d / "home" / arm, since):
            raise Pause(f"background limit: {hit[:300]}")
        # hooks never get the bench's token: a rival that calls claude from a hook logs out silently
        if hit := background_limited(d / "home" / arm, since, r"Not logged in", d / "wr" / arm):
            halt(f"{arm} background call not logged in: {hit[:300]}")
        if s["id"] == track(t)["S"][0]["id"] and sh("bash", str(CODE / "arms.sh"), "captured", env=env(t, arm), timeout=120).returncode:
            halt(f"{arm} store holds nothing after {t} {s['id']}; see arms.sh dump")
        names = {Path(f["path"]).name for f in s.get("plant", [])}
        tracked = sh("git", "-C", str(d / "wr" / arm), "log", "--all", "--name-only", "--format=").stdout
        if leaked := [n for n in names if n in tracked]:
            log(event="plant-leak", track=t, arm=arm, sid=s["id"], files=leaked)
        log(event="write", track=t, arm=arm, sid=s["id"], **m)
    except (Pause, Fail):
        arm_do(t, arm, "down")
        snap(t, arm, "pre", restore=True)
        raise
    finally:
        plant(s.get("plant", []), remove=True)
        arm_do(t, arm, "down")


def freeze(t: str, arm: str) -> None:
    arm_do(t, arm, "down")
    snap(t, arm, "eval")
    out = ROOT / t / "results" / f"memory_{arm}.txt"
    out.write_text(arm_do(t, arm, "dump"), encoding="utf-8")


def answer(t: str, q: dict, rep: int, arm: str) -> None:
    d = ROOT / t
    snap(t, arm, "eval", restore=True)
    (d / "results" / "eval").mkdir(parents=True, exist_ok=True)
    try:
        arm_do(t, arm, "evalmode")
        arm_do(t, arm, "up")
        m = claude([q["task"] + EVAL_SUFFIX], d / "wr" / arm, env(t, arm), d / "results" / "eval" / f"{arm}_{q['id']}_{rep}.jsonl",
                   "Edit Write NotebookEdit " + NO_TOOLS)
        log(event="eval", track=t, arm=arm, qid=q["id"], rep=rep, **m)
    finally:
        arm_do(t, arm, "down")


def result_of(path: Path) -> dict:
    out = {"answer": "", "cost": 0.0, "tokens": 0, "tools": 0}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("{"):
            continue
        ev = json.loads(line)
        if ev.get("type") == "assistant":
            out["tools"] += sum(c.get("type") == "tool_use" for c in ev["message"]["content"])
        elif ev.get("type") == "result":
            u = ev.get("usage", {})
            out["answer"] = ev.get("result") or ""
            out["cost"] += ev.get("total_cost_usd", 0.0)
            out["tokens"] += u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
    return out


def judge(t: str, model: str) -> None:
    cfg = track(t)
    qs = {q["id"]: q for q in cfg["Q"]}
    jhome = ROOT / "judge-home"
    jhome.mkdir(exist_ok=True)
    e = {k: v for k, v in os.environ.items() if not k.startswith("ANTHROPIC_")}
    e.update(HOME=str(jhome), CLAUDE_CODE_OAUTH_TOKEN=token(), CLAUDE_CODE_DISABLE_AUTO_MEMORY="1", DISABLE_AUTOUPDATER="1")
    for p in sorted((cfg["dir"] / "results" / "eval").glob("*.jsonl")):
        out = p.with_suffix(f".{model}.json")
        if out.exists():
            continue
        q = qs[p.stem.split("_")[1]]
        prompt = JUDGE.format(task=q["task"], points="\n".join(f"{i + 1}. {g}" for i, g in enumerate(q["gold"])),
                              answer=result_of(p)["answer"] or "(no answer)")
        verdict = None
        for _ in range(3):
            r = subprocess.run(["claude", "-p", "--model", model, "--output-format", "json", "--max-turns", "1",
                                "--disallowedTools", "Bash Read Write Edit Grep Glob " + NO_TOOLS],
                               cwd=jhome, env=e, input=prompt, capture_output=True, text=True, encoding="utf-8", timeout=600)
            try:
                res = json.loads(r.stdout)
            except json.JSONDecodeError:
                res = {"is_error": True, "result": r.stderr[-300:]}
            text = res.get("result") or ""
            if res.get("is_error"):
                raise Pause(f"judge {model}: {text[:300]}")
            found = re.findall(r"\{\"hits\".*\}", text)
            if found:
                verdict = json.loads(found[-1])
                if len(verdict["hits"]) == len(q["gold"]):
                    break
                verdict = None
        if verdict:
            out.write_text(json.dumps(verdict), encoding="utf-8")
        else:
            log(event="judge-no-verdict", track=t, file=p.name, model=model)


def boot(diffs: dict, n: int = 10000) -> tuple[float, float, float]:
    qs = list(diffs)
    mean = sum(map(sum, diffs.values())) / sum(map(len, diffs.values()))
    rng = random.Random(0)
    stats = sorted(
        sum(map(sum, pick)) / sum(map(len, pick))
        for pick in ([diffs[rng.choice(qs)] for _ in qs] for _ in range(n))
    )
    return mean, stats[int(0.025 * n)], stats[int(0.975 * n)]


def family(kind: str) -> str:
    f = kind.split("-")[0]
    return f if f in ("stated", "corrected", "discovered", "repo", "continuity") else "stated"


def report(t: str) -> str:
    cfg = track(t)
    qs = {q["id"]: q for q in cfg["Q"]}
    rows = defaultdict(dict)
    for p in sorted((cfg["dir"] / "results" / "eval").glob("*.jsonl")):
        arm, qid, rep = p.stem.split("_")
        vs = [json.loads(v.read_text(encoding="utf-8")) for m in PLAN["judges"] if (v := p.with_suffix(f".{m}.json")).exists()]
        if not vs:
            continue
        r = result_of(p)
        rows[(qid, rep)][arm] = {"score": sum(sum(v["hits"]) / len(v["hits"]) for v in vs) / len(vs),
                                 "wrong": sum(v["wrong"] for v in vs) / len(vs), "judges": len(vs), **r}
    lines = [f"# {t}  (model {MODEL}; score = mean over available judges; {len(rows)} question-runs judged)"]
    fams = sorted({family(q["kind"]) for q in cfg["Q"]})
    for fam in ["all", *fams]:
        sel = {k: v for k, v in rows.items() if fam == "all" or family(qs[k[0]]["kind"]) == fam}
        if not sel:
            continue
        lines.append(f"\n## {fam}\n{'arm':<4}{'n':>5}{'score':>8}{'wrong':>8}{'tokens':>10}{'tools':>7}{'cost':>8}")
        for arm in cfg["arms"]:
            r = [v[arm] for v in sel.values() if arm in v]
            if r:
                lines.append(f"{arm:<4}{len(r):>5}" + "".join(f"{sum(x[k] for x in r) / len(r):>{w}.{p}f}" for k, w, p in
                             (("score", 8, 2), ("wrong", 8, 2), ("tokens", 10, 0), ("tools", 7, 1), ("cost", 8, 3))))
        for ref in ("D", "D0"):
            for other in cfg["arms"]:
                if ref not in cfg["arms"] or other in (ref, "D") or (ref == "D0" and other != "N"):
                    continue
                diffs = defaultdict(list)
                for (qid, _), v in sel.items():
                    if ref in v and other in v:
                        diffs[qid].append(v[ref]["score"] - v[other]["score"])
                if diffs:
                    m, lo, hi = boot(diffs)
                    lines.append(f"{ref}-{other}: {m:+.2f}  95% CI [{lo:+.2f}, {hi:+.2f}]  ({len(diffs)} questions)")
    lines.append(f"\n## per question ({' / '.join(cfg['arms'])})")
    for qid, q in qs.items():
        cells = []
        for arm in cfg["arms"]:
            s = [v[arm]["score"] for (k, _), v in rows.items() if k == qid and arm in v]
            cells.append(f"{sum(s) / len(s):.2f}" if s else "  - ")
        lines.append(f"{qid:<4}{q['kind'][:24]:<25}" + " / ".join(cells))
    text = "\n".join(lines) + "\n"
    out = CODE / "results" / t
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.txt").write_text(text, encoding="utf-8")
    with (out / "answers.jsonl").open("w", encoding="utf-8") as f:
        for (qid, rep), v in sorted(rows.items()):
            for arm, r in v.items():
                f.write(json.dumps({"arm": arm, "qid": qid, "rep": rep, **r}) + "\n")
    for p in (cfg["dir"] / "results").glob("*.txt"):
        shutil.copy(p, out / p.name)
    return text


def jobs() -> list[tuple]:
    out = []
    for t in PLAN["order"]:
        cfg = track(t)
        arms = cfg["arms"]
        out += [(f"{t}:setup:{a}", setup, (t, a)) for a in arms]
        if MIMI & set(arms):
            out.append((f"{t}:build", build, (t,)))
        out += [(f"{t}:write:{s['id']}:{a}", write, (t, a, s)) for s in cfg["S"] for a in arms]
        out += [(f"{t}:freeze:{a}", freeze, (t, a)) for a in arms]
        for rep in range(max(reps(cfg, q["id"]) for q in cfg["Q"])):
            out += [(f"{t}:eval:{q['id']}:{rep}:{a}", answer, (t, q, rep, a)) for q in cfg["Q"] if rep < reps(cfg, q["id"]) for a in arms]
        out.append((f"{t}:judge:{PLAN['judges'][0]}", judge, (t, PLAN["judges"][0])))
        out.append((f"{t}:report:1", report, (t,)))
    for t in PLAN["order"]:
        out += [(f"{t}:judge:{m}", judge, (t, m)) for m in PLAN["judges"][1:]]
        out.append((f"{t}:report:2", report, (t,)))
    return out


def done_path(jid: str) -> Path:
    return ROOT / "done" / jid.replace(":", "__")


def proxies() -> None:
    for a in ALL_ARMS:
        if sh("pgrep", "-f", f"proxy.py {port(a)}").returncode:
            subprocess.Popen(["python3", str(CODE.parent / "harness" / "proxy.py"), str(port(a)), str(ROOT / f"proxy_{a}.jsonl")],
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)


def tick(only: str = "") -> None:
    ROOT.mkdir(exist_ok=True)
    (ROOT / "done").mkdir(exist_ok=True)
    lock = (ROOT / ".lock").open("w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("another tick is running", flush=True)
        return
    if (ROOT / "halt").exists():
        print(f"halted, delete {ROOT / 'halt'} to resume: {(ROOT / 'halt').read_text()}", flush=True)
        return
    over = ROOT / "overage_until"
    if over.exists() and time.time() < float(over.read_text()):
        print(f"on paid overage until {time.strftime('%H:%M UTC', time.gmtime(float(over.read_text())))}", flush=True)
        return
    proxies()
    fails_p = ROOT / "fails.json"
    fails = json.loads(fails_p.read_text()) if fails_p.exists() else {}
    # BENCH_ARMS=D,M runs only those arms; judge and report then run without being marked done
    arms = set(filter(None, os.environ.get("BENCH_ARMS", "").split(",")))
    for jid, fn, args in jobs():
        if done_path(jid).exists() or fails.get(jid, 0) >= 3 or (only and not jid.startswith(only)):
            continue
        arm = "D" if jid.endswith(":build") else jid.split(":")[-1]
        partial = arms and arm not in ALL_ARMS
        if arms and arm in ALL_ARMS and arm not in arms:
            continue
        t0 = time.time()
        try:
            fn(*args)
        except Pause as p:
            log(event="pause", job=jid, reason=str(p))
            (ROOT / "paused.json").write_text(json.dumps({"ts": time.time(), "job": jid, "reason": str(p)}))
            return
        except Exception as ex:
            fails[jid] = fails.get(jid, 0) + 1
            fails_p.write_text(json.dumps(fails, indent=1))
            log(event="fail", job=jid, tries=fails[jid], error=f"{type(ex).__name__}: {ex}"[:1500])
            return
        if not partial:
            done_path(jid).touch()
        log(event="done", job=jid, secs=round(time.time() - t0), partial=bool(partial))
        # an account with extra usage on keeps answering past the 5-hour limit and bills it: wait for the reset
        if OVERAGE:
            over.write_text(str(OVERAGE["resetsAt"]))
            log(event="pause", job=jid, reason=f"paid overage until {OVERAGE['resetsAt']}")
            return
        if only == jid:
            return
    log(event="all-done")


def status() -> None:
    fails_p = ROOT / "fails.json"
    fails = json.loads(fails_p.read_text()) if fails_p.exists() else {}
    per = defaultdict(lambda: [0, 0, 0])
    nxt = None
    for jid, *_ in jobs():
        t = jid.split(":")[0]
        if done_path(jid).exists():
            per[t][0] += 1
        elif fails.get(jid, 0) >= 3:
            per[t][2] += 1
        else:
            per[t][1] += 1
            nxt = nxt or jid
    for t, (d, p, f) in per.items():
        print(f"{t:<12} done {d:>4}  pending {p:>4}  failed {f:>3}")
    print("next:", nxt)
    if (ROOT / "halt").exists():
        print("HALTED:", (ROOT / "halt").read_text()[:300])
    if (ROOT / "paused.json").exists():
        p = json.loads((ROOT / "paused.json").read_text())
        print(f"last pause: {time.strftime('%Y-%m-%d %H:%M', time.localtime(p['ts']))} at {p['job']}: {p['reason'][:200]}")
    spent, quota = defaultdict(float), None
    if (ROOT / "jobs.log").exists():
        for line in (ROOT / "jobs.log").read_text(encoding="utf-8").splitlines():
            ev = json.loads(line)
            if ev.get("five_hour") is not None:
                quota = (ev["five_hour"], ev["seven_day"] or 0)
            if "cost" in ev:
                spent[time.strftime("%Y-%m-%d %H:00", time.localtime(ev["ts"]))] += ev["cost"]
    if quota:
        print(f"quota used at last job: 5-hour {quota[0]:.0%}, weekly {quota[1]:.0%}")
    for hour, c in sorted(spent.items())[-12:]:
        print(f"  {hour}  ${c:.2f} API-equivalent")


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "tick":
        tick(sys.argv[2] if len(sys.argv) > 2 else "")
    elif cmd == "status":
        status()
    elif cmd == "report":
        for t in sys.argv[2:] or PLAN["order"]:
            print(report(t))
    elif cmd == "jobs":
        for jid, *_ in jobs():
            print(("done " if done_path(jid).exists() else "     ") + jid)
    else:
        sys.exit("usage: bench.py tick [job-id-prefix] | status | report [track...] | jobs")


if __name__ == "__main__":
    main()
