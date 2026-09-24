import difflib
import re
import sys
from pathlib import Path

WORK, SNAP = Path(sys.argv[1]), Path(sys.argv[2])
FACTS = {
    "aix-7.2-tl5": r"7\.2\s*TL\s*5",
    "ram-4gb": r"\b4\s*GB",
    "ram-16gb": r"\b16\s*GB",
    "no-backport-v22": r"56\s*KiB",
    "startup-38.4ms": r"38\.4",
    "noexec-tmp": r"noexec",
}


def docs(root: Path) -> dict[str, str]:
    return {
        str(p.relative_to(root)): p.read_text(encoding="utf-8", errors="replace")
        for p in root.rglob("*.md")
        if ".git" not in p.parts and ".claude" not in p.parts
    }


for arm in sorted(p.name for p in WORK.iterdir()):
    before, after = docs(SNAP / arm), docs(WORK / arm)
    print(f"\n===== {arm}")
    added = removed = 0
    for name in sorted(set(before) | set(after)):
        a, b = before.get(name, "").splitlines(), after.get(name, "").splitlines()
        if a == b:
            continue
        d = list(difflib.unified_diff(a, b, lineterm="", n=0))
        plus = sum(l.startswith("+") and not l.startswith("+++") for l in d)
        minus = sum(l.startswith("-") and not l.startswith("---") for l in d)
        added, removed = added + plus, removed + minus
        print(f"  {name}: +{plus} -{minus}")
    print(f"  TOTAL memory lines +{added} -{removed}, net {added - removed:+d}")
    for fact, pat in FACTS.items():
        hits = {n: len(re.findall(pat, t, re.I)) - len(re.findall(pat, before.get(n, ""), re.I)) for n, t in after.items()}
        hits = {n: c for n, c in hits.items() if c > 0}
        print(f"  {fact:<14} new mentions in {len(hits)} file(s): {hits}")
