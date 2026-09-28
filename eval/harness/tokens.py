import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

KEYS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")


def tally():
    return defaultdict(lambda: dict.fromkeys((*KEYS, "calls"), 0))


def add(row: dict, usage: dict) -> None:
    for k in KEYS:
        row[k] += usage.get(k) or 0
    row["calls"] += 1


def account(home: Path, plog: Path, phases: dict) -> dict:
    def phase(ts: float) -> str:
        return next((name for name, (a, b) in phases.items() if a <= ts <= b), "other")

    out = {src: defaultdict(tally) for src in ("proxy", "main", "worker")}
    if plog.exists():
        for line in plog.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if r["usage"]:
                add(out["proxy"][phase(r["ts"])][r["model"]], r["usage"])
    seen = set()
    for p in (home / ".claude" / "projects").rglob("*.jsonl"):
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = ev.get("message") or {}
            if ev.get("type") != "assistant" or msg.get("id") in seen or not msg.get("usage"):
                continue
            seen.add(msg.get("id"))
            src = "worker" if ev.get("entrypoint") == "sdk-ts" else "main"
            ts = datetime.fromisoformat(ev["timestamp"]).timestamp()
            add(out[src][phase(ts)][msg.get("model", "")], msg["usage"])
    return out


def main() -> None:
    home, plog, phases = Path(sys.argv[1]), Path(sys.argv[2]), json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
    out = account(home, plog, phases)
    print(json.dumps(out, indent=1))
    print(f"\n{'phase':<8}{'source':<8}{'model':<34}{'calls':>7}" + "".join(f"{k:>12}" for k in ("input", "cache_write", "cache_read", "output")), file=sys.stderr)
    for src, by_phase in out.items():
        for ph, by_model in sorted(by_phase.items()):
            for model, row in sorted(by_model.items()):
                print(f"{ph:<8}{src:<8}{model[:33]:<34}{row['calls']:>7}" + "".join(f"{row[k]:>12,}" for k in KEYS), file=sys.stderr)


if __name__ == "__main__":
    main()
