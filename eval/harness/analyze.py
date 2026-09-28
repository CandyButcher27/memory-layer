import json
import random
import sys
from collections import defaultdict
from pathlib import Path

JUDGES = ("sonnet", "opus")
ARMS = "ANDM"
PAIRS = (("D", "M"), ("D", "N"), ("D", "A"), ("M", "N"))


def load(roots: list[Path]) -> dict:
    rows = defaultdict(dict)
    for root in roots:
        for p in (root / "results_eval").glob("*.jsonl"):
            arm, tid, rep = p.stem.split("_")
            vs = [p.with_suffix(f".v2.{j}.json") for j in JUDGES]
            if not all(v.exists() for v in vs):
                continue
            hits = [json.loads(v.read_text(encoding="utf-8"))["hits"] for v in vs]
            wrong = json.loads(vs[0].read_text(encoding="utf-8"))["wrong"]
            cost = tokens = 0.0
            for line in p.read_text(encoding="utf-8").splitlines():
                if '"type":"result"' in line:
                    ev = json.loads(line)
                    u = ev.get("usage", {})
                    cost += ev.get("total_cost_usd", 0.0)
                    tokens += u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
            score = sum(sum(h) / len(h) for h in hits) / len(hits)
            rows[(root.name, tid, rep)][arm] = {"score": score, "wrong": wrong, "cost": cost, "tokens": tokens}
    return rows


def family(tid: str) -> str:
    return "F2" if tid.startswith("C") else "F1"


def boot(diffs_by_q: dict, n: int = 10000) -> tuple[float, float, float]:
    qs = list(diffs_by_q)
    mean = sum(sum(v) for v in diffs_by_q.values()) / sum(len(v) for v in diffs_by_q.values())
    rng = random.Random(0)
    stats = []
    for _ in range(n):
        pick = [diffs_by_q[rng.choice(qs)] for _ in qs]
        stats.append(sum(sum(v) for v in pick) / sum(len(v) for v in pick))
    stats.sort()
    return mean, stats[int(0.025 * n)], stats[int(0.975 * n)]


def main() -> None:
    rows = load([Path(a) for a in sys.argv[1:]])
    for fam in ("F1", "F2"):
        sel = {k: v for k, v in rows.items() if family(k[1]) == fam}
        print(f"\n== {fam} ({len(sel)} question-runs)")
        print(f"{'arm':<4}{'n':>5}{'score':>8}{'wrong':>8}{'tokens':>10}{'cost':>8}")
        for arm in ARMS:
            r = [v[arm] for v in sel.values() if arm in v]
            if r:
                print(f"{arm:<4}{len(r):>5}" + "".join(f"{sum(x[k] for x in r) / len(r):>{w}.{d}f}" for k, w, d in (("score", 8, 2), ("wrong", 8, 2), ("tokens", 10, 0), ("cost", 8, 3))))
        for a, b in PAIRS:
            diffs = defaultdict(list)
            for (repo, tid, _), v in sel.items():
                if a in v and b in v:
                    diffs[(repo, tid)].append(v[a]["score"] - v[b]["score"])
            if diffs:
                m, lo, hi = boot(diffs)
                print(f"{a}-{b}: {m:+.2f}  95% CI [{lo:+.2f}, {hi:+.2f}]  ({len(diffs)} questions)")
        print("per question (A / N / D / M):")
        for key in sorted({(k[0], k[1]) for k in sel}):
            cells = []
            for arm in ARMS:
                s = [v[arm]["score"] for k, v in sel.items() if (k[0], k[1]) == key and arm in v]
                cells.append(f"{sum(s) / len(s):.2f}" if s else "-")
            print(f"  {key[0]:<13}{key[1]:<4}" + " / ".join(cells))


if __name__ == "__main__":
    main()
