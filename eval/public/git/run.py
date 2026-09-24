import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARMS_ROOT = Path(sys.argv[2]) if len(sys.argv) > 2 else None
RESULTS = HERE / os.environ.get("RESULTS", "results")
TASKS = {t["id"]: t for t in json.loads((HERE / os.environ.get("TASKS", "tasks.json")).read_text(encoding="utf-8"))}
ARMS = tuple(os.environ.get("ARMS", "ABC"))
SUFFIX = (
    "\n\nAnswer from this repository. Do not modify any file, and do not connect to a database or"
    " the network. Keep the answer under 200 words and cite the files or commits you relied on."
)
WRITE_SUFFIX = (
    "\n\nWork in this repository. Do not connect to a database or the network. Commit your code changes"
    " on the current branch. Before you finish, update this project's memory the way its CLAUDE.md says to."
)
SEARCH_TOOLS = {"Grep", "Glob"}


def run_one(arm: str, tid: str, rep: int, write: bool = False) -> Path:
    out = RESULTS / f"{arm}_{tid}_{rep}.jsonl"
    if out.exists() and '"is_error":false' in out.read_text(encoding="utf-8"):
        return out
    cmd = [
        "claude", "-p", TASKS[tid]["task"] + (WRITE_SUFFIX if write else SUFFIX),
        "--output-format", "stream-json", "--verbose",
        "--allowedTools", "Read Grep Glob Bash Edit Write Skill" if write else "Read Grep Glob Bash",
        "--disallowedTools", ("" if write else "Edit Write ") + "NotebookEdit Agent Workflow WebFetch WebSearch",
        "--max-turns", "40",
    ] + (["--model", os.environ["MODEL"]] if os.environ.get("MODEL") else [])
    with out.open("w", encoding="utf-8") as f:
        subprocess.run(cmd, cwd=ARMS_ROOT / arm, stdin=subprocess.DEVNULL, stdout=f, stderr=subprocess.DEVNULL, timeout=1200)
    return out


def metrics(path: Path) -> dict:
    tools, result = [], {}
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "assistant":
            tools += [c["name"] for c in ev["message"]["content"] if c.get("type") == "tool_use"]
        elif ev.get("type") == "result":
            result = ev
    u = result.get("usage", {})
    return {
        "answer": result.get("result", ""),
        "tools": len(tools),
        "search": sum(t in SEARCH_TOOLS for t in tools),
        "bash": tools.count("Bash"),
        "reads": tools.count("Read"),
        "input_tokens": u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0),
        "cost": result.get("total_cost_usd", 0.0),
        "seconds": result.get("duration_ms", 0) / 1000,
    }


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


def judge_one(path: Path, model: str = "sonnet", suffix: str = ".judge.json") -> dict:
    out = path.with_suffix(suffix)
    if out.exists():
        return json.loads(out.read_text(encoding="utf-8"))
    tid = path.stem.split("_")[1]
    t = TASKS[tid]
    prompt = JUDGE.format(
        task=t["task"],
        points="\n".join(f"{i + 1}. {p}" for i, p in enumerate(t["gold"])),
        answer=metrics(path)["answer"] or "(no answer)",
    )
    for _ in range(3):
        r = subprocess.run(
            ["claude", "-p", "--model", model, "--output-format", "json", "--max-turns", "1"],
            cwd=ARMS_ROOT, input=prompt, capture_output=True, text=True, encoding="utf-8", timeout=600,
        )
        try:
            text = json.loads(r.stdout).get("result") or ""
        except json.JSONDecodeError:
            text = ""
        m = re.search(r"\{\"hits\".*\}", text, re.S)
        if m:
            break
    if not m:
        print(f"judge {model} gave no verdict for {path.name}", flush=True)
        return {}
    verdict = json.loads(m[0])
    assert len(verdict["hits"]) == len(t["gold"]), verdict
    out.write_text(json.dumps(verdict), encoding="utf-8")
    return verdict


def report() -> None:
    rows = {a: [] for a in ARMS}
    for p in sorted(RESULTS.glob("*.jsonl")):
        j = p.with_suffix(".judge.json")
        if not j.exists():
            j = p.with_suffix(".v2.sonnet.json")
        if not j.exists():
            continue
        arm, tid, _ = p.stem.split("_")
        if arm not in rows or tid not in TASKS:
            continue
        v = json.loads(j.read_text(encoding="utf-8"))
        rows[arm].append({"tid": tid, "score": sum(v["hits"]) / len(v["hits"]), "wrong": v["wrong"], **metrics(p)})
    cols = ("score", "wrong", "tools", "search", "bash", "reads", "input_tokens", "cost", "seconds")
    print(f"{'arm':<4}{'n':>4}" + "".join(f"{c:>14}" for c in cols))
    for arm, rs in rows.items():
        if rs:
            print(f"{arm:<4}{len(rs):>4}" + "".join(f"{sum(r[c] for r in rs) / len(rs):>14.2f}" for c in cols))
    print(f"\nper task score ({' / '.join(ARMS)}):")
    for tid in TASKS:
        cell = [f"{sum(r['score'] for r in rows[a] if r['tid'] == tid) / max(1, sum(r['tid'] == tid for r in rows[a])):.2f}" for a in ARMS]
        print(f"{tid} {TASKS[tid]['kind']:<16} " + " / ".join(cell))


JUDGES = ("sonnet", "opus")


def judge2(path: Path) -> None:
    for model in JUDGES:
        judge_one(path, model, f".v2.{model}.json")


def report2() -> None:
    rows = {a: [] for a in ARMS}
    split = []
    for p in sorted(RESULTS.glob("*.jsonl")):
        arm, tid, _ = p.stem.split("_")
        vs = [p.with_suffix(f".v2.{m}.json") for m in JUDGES]
        if arm not in rows or tid not in TASKS or not all(v.exists() for v in vs):
            continue
        hits = [json.loads(v.read_text(encoding="utf-8"))["hits"] for v in vs]
        diff = sum(a != b for a, b in zip(*hits))
        rows[arm].append([sum(h) / len(h) for h in hits] + [diff / len(hits[0])])
        if diff:
            split.append(f"{p.stem}: " + " vs ".join(f"{m}={h}" for m, h in zip(JUDGES, hits)))
    print(f"{'arm':<4}{'n':>4}" + "".join(f"{c:>12}" for c in (*JUDGES, "mean", "disagree")))
    for arm, rs in rows.items():
        if rs:
            cols = [sum(r[i] for r in rs) / len(rs) for i in range(3)]
            print(f"{arm:<4}{len(rs):>4}{cols[0]:>12.2f}{cols[1]:>12.2f}{(cols[0] + cols[1]) / 2:>12.2f}{cols[2]:>12.2f}")
    print(f"\n{len(split)} answers where the judges disagree on a key point:")
    print("\n".join(split))


def main() -> None:
    usage = "usage: run.py run <arms_root> [task_ids,comma] [reps] [parallel] | session <arms_root> | judge <arms_root> | judge2 <arms_root> | report | report2"
    if len(sys.argv) < 2 or sys.argv[1] not in ("run", "session", "judge", "judge2", "report", "report2"):
        sys.exit(usage)
    RESULTS.mkdir(exist_ok=True)
    if sys.argv[1] == "report":
        report()
        return
    if sys.argv[1] == "report2":
        report2()
        return
    if sys.argv[1] == "judge2":
        with ThreadPoolExecutor(3) as ex:
            list(ex.map(judge2, sorted(RESULTS.glob("*.jsonl"))))
        report2()
        return
    if sys.argv[1] == "session":
        with ThreadPoolExecutor(len(ARMS)) as ex:
            list(ex.map(lambda a: [run_one(a, t, 0, write=True) for t in TASKS], ARMS))
        return
    if sys.argv[1] == "judge":
        paths = sorted(RESULTS.glob("*.jsonl"))
        with ThreadPoolExecutor(4) as ex:
            list(ex.map(judge_one, paths))
        report()
        return
    tids = sys.argv[3].split(",") if len(sys.argv) > 3 and sys.argv[3] != "all" else list(TASKS)
    reps = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    par = int(sys.argv[5]) if len(sys.argv) > 5 else 3
    jobs = [(a, t, r) for r in range(reps) for t in tids for a in ARMS]
    with ThreadPoolExecutor(par) as ex:
        for p in ex.map(lambda j: run_one(*j), jobs):
            print(p.name, {k: v for k, v in metrics(p).items() if k != "answer"}, flush=True)


if __name__ == "__main__":
    main()
