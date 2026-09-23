import re
import sys
import tempfile
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATES = HERE / "templates"
START = "<!-- memory-layer:start -->"
SEEDED = ("STATE.md", "ISSUES.md", "decisions.md", "memory/external.md")
CAPS = {"CLAUDE.md": 100, "STATE.md": 60}
MEMORY_CAP = 150
STALE_DAYS = 90
VERIFIED = re.compile(r"Last verified:\s*(\d{4}-\d{2}-\d{2})")
COMMENT = re.compile(r"<!--.*?-->", re.S)
INDEX_LINE = re.compile(r"^(- .*?→ `(memory/[\w.-]+\.md)`)(?: — contains: .*)?$", re.M)
HEADING = re.compile(r"^#{2,3} (.+)$", re.M)


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


def render(name: str) -> str:
    text = (TEMPLATES / name).read_text(encoding="utf-8")
    return text.replace("{today}", date.today().isoformat()).replace("{memlayer}", HERE.joinpath("memlayer.py").as_posix())


def init(root: Path) -> list[str]:
    done = []
    for name in SEEDED:
        dst = root / name
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(render(name), encoding="utf-8")
            done.append(f"created {name}")
    claude = root / "CLAUDE.md"
    text = read(claude)
    if START not in text:
        sep = "\n\n" if text.strip() else ""
        claude.write_text(text.rstrip() + sep + render("CLAUDE-block.md"), encoding="utf-8")
        done.append("added memory block to CLAUDE.md")
    return done


def index(root: Path) -> bool:
    claude = root / "CLAUDE.md"
    text = read(claude)

    def fill(m: re.Match) -> str:
        heads = HEADING.findall(COMMENT.sub("", read(root / m[2])))
        return m[1] + (f" — contains: {'; '.join(h.strip() for h in heads)}" if heads else "")

    new = INDEX_LINE.sub(fill, text)
    if new != text:
        claude.write_text(new, encoding="utf-8")
    return new != text


def check(root: Path) -> list[str]:
    problems = []
    for name, cap in CAPS.items():
        p = root / name
        if not p.exists():
            problems.append(f"{name}: missing, run init")
        elif (n := len(read(p).splitlines())) > cap:
            problems.append(f"{name}: {n} lines, cap {cap}")
    claude = read(root / "CLAUDE.md")
    for p in sorted((root / "memory").glob("*.md")):
        rel = f"memory/{p.name}"
        text = read(p)
        if (n := len(text.splitlines())) > MEMORY_CAP:
            problems.append(f"{rel}: {n} lines, cap {MEMORY_CAP}, split by topic")
        if rel not in claude:
            problems.append(f"{rel}: not in the CLAUDE.md index, so it is never read")
        m = VERIFIED.search(text)
        if not m:
            problems.append(f"{rel}: no 'Last verified: YYYY-MM-DD' line")
        elif (age := (date.today() - date.fromisoformat(m[1])).days) > STALE_DAYS:
            problems.append(f"{rel}: last verified {age} days ago, re-check it against reality")
    for ref in sorted(set(re.findall(r"memory/[\w.-]+\.md", claude))):
        if not (root / ref).exists():
            problems.append(f"CLAUDE.md: points to {ref}, which does not exist")
    issues = COMMENT.sub("", read(root / "ISSUES.md"))
    for entry in re.split(r"^(?=#+ )", issues, flags=re.M):
        if entry.startswith("## ISS-") and ("Symptom:" not in entry or "Cause:" not in entry):
            problems.append(f"ISSUES.md: '{entry.splitlines()[0][3:]}' needs Symptom: and Cause:")
    return problems


def selftest() -> None:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "CLAUDE.md").write_text("# Mine\nkeep me\n", encoding="utf-8")
        assert len(init(root)) == 5
        assert init(root) == []
        assert "keep me" in read(root / "CLAUDE.md")
        assert check(root) == [], check(root)
        (root / "memory/db.md").write_text("quirk\n", encoding="utf-8")
        assert len(check(root)) == 2, check(root)
        (root / "memory/db.md").write_text("Last verified: 2000-01-01\n", encoding="utf-8")
        assert any("days ago" in p for p in check(root))
        (root / "memory/db.md").unlink()
        (root / "ISSUES.md").write_text("# Issues\n## ISS-1 — x\nSymptom: boom\n", encoding="utf-8")
        assert check(root) == ["ISSUES.md: 'ISS-1 — x' needs Symptom: and Cause:"], check(root)
        (root / "ISSUES.md").write_text("# Issues\n", encoding="utf-8")
        ext = root / "memory/external.md"
        ext.write_text(read(ext) + "\n## stripe sends duplicate webhooks\n", encoding="utf-8")
        assert index(root) and "— contains: stripe sends duplicate webhooks" in read(root / "CLAUDE.md")
        assert not index(root)
        (root / "STATE.md").write_text("x\n" * 61, encoding="utf-8")
        assert check(root) == ["STATE.md: 61 lines, cap 60"], check(root)
    print("SELFTEST_OK")


def main() -> int:
    usage = "usage: memlayer.py init [dir] | index [dir] | check [dir] | selftest"
    if len(sys.argv) < 2 or sys.argv[1] not in ("init", "index", "check", "selftest"):
        print(usage)
        return 2
    if sys.argv[1] == "selftest":
        selftest()
        return 0
    root = Path(sys.argv[2] if len(sys.argv) > 2 else ".").resolve()
    if sys.argv[1] == "init":
        print("\n".join(init(root)) or "already initialised, nothing to do")
        return 0
    if sys.argv[1] == "index":
        print("index lines updated" if index(root) else "index already current")
        return 0
    problems = check(root)
    print("\n".join(problems) or "memory layer clean")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
