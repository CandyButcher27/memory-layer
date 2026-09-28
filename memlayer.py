import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
TEMPLATES = HERE / "templates"
START = "<!-- memory-layer:start -->"
END = "<!-- memory-layer:end -->"
SEEDED = ("STATE.md", "ISSUES.md", "decisions.md", "memory/external.md")
CAPS = {"CLAUDE.md": 100, "STATE.md": 60}
MEMORY_CAP = 150
AUTOLOAD_CAP = 16_000
STALE_DAYS = 90
VERIFIED = re.compile(r"Last verified:\s*(\S+)")
COMMENT = re.compile(r"<!--.*?-->", re.S)
FENCE = re.compile(r"^```.*?^```[^\n]*$", re.S | re.M)
INDEX_LINE = re.compile(r"^(- .*?→ `(memory/[^`]+\.md)`)(?: — (?:contains: .*|empty))?$", re.M)
TOP_LINE = re.compile(r"^(- .*?→ `(ISSUES\.md|decisions\.md)`.*?)(?: — empty)?$", re.M)
HEADING = re.compile(r"^#{2,3} (.+)$", re.M)
ISSUE = re.compile(r"^#{2,3} (ISS-.*)$", re.M)
CONFLICT = re.compile(r"^(<{7}|>{7})( |$)", re.M)
SEARCH_CMD = re.compile(r"\b(grep|rg|find|git grep|git log)\b")
BYTES_PER_TOKEN = 4
MIN_SESSIONS = 3


def load(p: Path) -> tuple[str, str]:
    if not p.exists():
        return "", "\n"
    with open(p, encoding="utf-8", newline="") as f:
        raw = f.read()
    return raw.replace("\r\n", "\n"), "\r\n" if "\r\n" in raw else "\n"


def read(p: Path) -> str:
    return load(p)[0]


def save(p: Path, text: str, eol: str = "\n") -> None:
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(text.replace("\n", eol))


def script_path() -> str:
    path = HERE / "memlayer.py"
    try:
        return "$HOME/" + path.relative_to(Path.home()).as_posix()
    except ValueError:
        return path.as_posix()


def render(name: str) -> str:
    text = (TEMPLATES / name).read_text(encoding="utf-8")
    return text.replace("{today}", date.today().isoformat()).replace("{memlayer}", script_path())


def is_empty(text: str) -> bool:
    body = COMMENT.sub("", text)
    return not any(l.strip() and not l.startswith("# ") and not l.startswith("Last verified:") for l in body.splitlines())


def block_span(text: str) -> tuple[int, int] | None:
    start = text.find(START)
    if start < 0:
        return None
    end = text.find(END, start)
    return start, len(text) if end < 0 else end + len(END)


def memory_files(root: Path) -> list[str]:
    return sorted(p.relative_to(root).as_posix() for p in (root / "memory").rglob("*.md"))


def init(root: Path) -> list[str]:
    done = []
    for name in SEEDED:
        dst = root / name
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            save(dst, render(name))
            done.append(f"created {name}")
    claude = root / "CLAUDE.md"
    text, eol = load(claude)
    if START not in text:
        sep = "\n\n" if text.strip() else ""
        save(claude, text.rstrip() + sep + render("CLAUDE-block.md"), eol)
        done.append("added memory block to CLAUDE.md")
    index(root)
    return done


def indexed(root: Path, text: str) -> str:
    span = block_span(text)
    if not span:
        return text

    def fill(m: re.Match) -> str:
        body = COMMENT.sub("", read(root / m[2]))
        heads = HEADING.findall(body)
        if heads:
            return m[1] + f" — contains: {'; '.join(h.strip() for h in heads)}"
        return m[1] + (" — empty" if is_empty(body) else "")

    def mark(m: re.Match) -> str:
        return m[1] + (" — empty" if is_empty(read(root / m[2])) else "")

    a, b = span
    return text[:a] + TOP_LINE.sub(mark, INDEX_LINE.sub(fill, text[a:b])) + text[b:]


def index(root: Path) -> bool | None:
    claude = root / "CLAUDE.md"
    text, eol = load(claude)
    if not block_span(text):
        return None
    new = indexed(root, text)
    if new != text:
        save(claude, new, eol)
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
    span = block_span(claude)
    block = claude[span[0]:span[1]] if span else ""
    refs = {m[2] for m in INDEX_LINE.finditer(block)}
    autoload = sum(len(read(root / n).encode("utf-8")) for n in ("CLAUDE.md", "STATE.md"))
    if autoload > AUTOLOAD_CAP:
        problems.append(f"CLAUDE.md + STATE.md: {autoload:,} bytes load into every session, cap {AUTOLOAD_CAP:,}; merge memory files or shorten headings")
    if span and indexed(root, claude) != claude:
        problems.append("CLAUDE.md: index lines are stale, run index")
    for rel in memory_files(root):
        text = read(root / rel)
        if "/" in rel[len("memory/"):]:
            problems.append(f"{rel}: in a subfolder of memory/; works, but a flat memory/ is easier to scan")
        if (n := len(text.splitlines())) > MEMORY_CAP:
            problems.append(f"{rel}: {n} lines, cap {MEMORY_CAP}, split by topic")
        if rel not in refs:
            problems.append(f"{rel}: not in the CLAUDE.md index, so it is never read")
        dates = VERIFIED.findall(text)
        if not dates:
            problems.append(f"{rel}: no 'Last verified: YYYY-MM-DD' line")
        elif len(dates) > 1:
            problems.append(f"{rel}: {len(dates)} 'Last verified:' lines, keep one")
        else:
            try:
                age = (date.today() - date.fromisoformat(dates[0])).days
            except ValueError:
                problems.append(f"{rel}: 'Last verified: {dates[0]}' is not a YYYY-MM-DD date")
            else:
                if age < 0:
                    problems.append(f"{rel}: 'Last verified: {dates[0]}' is in the future")
                elif age > STALE_DAYS:
                    problems.append(f"{rel}: last verified {age} days ago, re-check it against reality")
    for ref in sorted(refs):
        if not (root / ref).exists():
            problems.append(f"CLAUDE.md: points to {ref}, which does not exist")
    issues = FENCE.sub("", COMMENT.sub("", read(root / "ISSUES.md")))
    for entry in re.split(r"^(?=#{1,6} )", issues, flags=re.M):
        m = ISSUE.match(entry)
        if m and ("Symptom:" not in entry or "Cause:" not in entry):
            problems.append(f"ISSUES.md: '{m[1].strip()}' needs Symptom: and Cause:")
    for rel in ("CLAUDE.md", "STATE.md", "ISSUES.md", "decisions.md", *memory_files(root)):
        if CONFLICT.search(read(root / rel)):
            problems.append(f"{rel}: contains git conflict markers")
    return problems


def transcript_dir(root: Path) -> Path:
    home = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    return home / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(root))


def session(path: Path, root: Path) -> dict:
    s = {"start": None, "prompts": 0, "closes": 0, "input": 0, "cached": 0, "output": 0, "tools": 0, "searches": 0, "init": False, "reads": Counter()}
    usage, tools = {}, {}
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("isSidechain") or ev.get("type") not in ("user", "assistant"):
                continue
            s["start"] = s["start"] or ev.get("timestamp")
            msg = ev.get("message") or {}
            content = msg.get("content") or []
            if ev["type"] == "assistant":
                usage[msg.get("id")] = msg.get("usage") or {}
                tools.update((c["id"], c) for c in content if isinstance(c, dict) and c.get("type") == "tool_use")
                continue
            if isinstance(content, str):
                text = content
            else:
                text = " ".join(c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text")
            if text.strip() and not ev.get("isMeta") and not ev.get("isCompactSummary") and not text.startswith("<local-command"):
                s["prompts"] += 1
                s["closes"] += "<command-name>/mimi-close" in text
    for u in usage.values():
        s["input"] += u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)
        s["cached"] += u.get("cache_read_input_tokens", 0)
        s["output"] += u.get("output_tokens", 0)
    for t in tools.values():
        args = t.get("input") or {}
        cmd = str(args.get("command", ""))
        s["tools"] += 1
        s["searches"] += t.get("name") in ("Grep", "Glob") or (t.get("name") == "Bash" and bool(SEARCH_CMD.search(cmd)))
        s["init"] |= "memlayer.py" in cmd and " init" in cmd
        if t.get("name") == "Read" and args.get("file_path"):
            try:
                rel = (root / args["file_path"]).resolve().relative_to(root).as_posix()
            except (ValueError, OSError):
                continue
            if rel in ("ISSUES.md", "decisions.md") or rel.startswith("memory/"):
                s["reads"][rel] += 1
    return s


def sessions(root: Path) -> list[dict]:
    found = [session(p, root) for p in sorted(transcript_dir(root).glob("*.jsonl"))]
    found = [s for s in found if s["start"] and s["prompts"]]
    for s in found:
        s["start"] = datetime.fromisoformat(s["start"]).astimezone()
    return sorted(found, key=lambda s: s["start"])


def adopted(root: Path, found: list[dict]) -> datetime | None:
    dates = [s["start"] for s in found if s["init"]]
    try:
        out = subprocess.run(["git", "log", "--reverse", "--format=%cI", "-S", START, "--", "CLAUDE.md"],
                             cwd=root, capture_output=True, text=True).stdout.split()
    except OSError:
        out = []
    if out:
        dates.append(datetime.fromisoformat(out[0]).astimezone())
    return min(dates, default=None)


def per_prompt(group: list[dict], key: str) -> float:
    return median(s[key] / s["prompts"] for s in group)


def stats(root: Path) -> str:
    if not block_span(read(root / "CLAUDE.md")):
        return "no memory-layer block in CLAUDE.md, run /mimi-start first"
    layer = [n for n in ("CLAUDE.md", "STATE.md", "ISSUES.md", "decisions.md") if (root / n).exists()] + memory_files(root)
    texts = {rel: read(root / rel) for rel in layer}
    lines = sum(len(t.splitlines()) for t in texts.values())
    size = sum(len(t.encode("utf-8")) for t in texts.values())
    autoload = sum(len(texts.get(n, "").encode("utf-8")) for n in ("CLAUDE.md", "STATE.md")) // BYTES_PER_TOKEN
    heads = {rel: len(HEADING.findall(COMMENT.sub("", t))) for rel, t in texts.items()}
    traps = sum(n for rel, n in heads.items() if rel.startswith("memory/"))
    empty = [rel for rel in layer if rel not in ("CLAUDE.md", "STATE.md") and is_empty(texts[rel])]
    closed = re.search(r"Last updated:\s*(\d{4}-\d{2}-\d{2})", texts.get("STATE.md", ""))
    out = [
        f"mimi stats for {root}",
        "",
        "Memory",
        f"  {len(layer)} files, {lines} lines, {size / 1000:.1f} KB",
        f"  loaded into every session: CLAUDE.md + STATE.md ~ {autoload:,} tokens",
        f"  {heads.get('ISSUES.md', 0)} issues, {heads.get('decisions.md', 0)} decisions, {traps} traps in memory/, {len(empty)} empty files",
        f"  STATE.md last updated: {closed[1] if closed else 'never'}",
    ]
    found = sessions(root)
    where = transcript_dir(root)
    if not found:
        return "\n".join(out + ["", f"No Claude Code sessions found in {where}"])
    since = adopted(root, found)
    before = [s for s in found if since and s["start"] < since]
    after = [s for s in found if not since or s["start"] >= since]
    def total(group: list[dict], key: str) -> int:
        return sum(s[key] for s in group)

    out += [
        "",
        f"Sessions ({len(found)} transcripts in {where})",
        f"  mimi adopted: {since.date() if since else 'unknown, no init in transcripts or git history'}",
        f"  since then: {len(after)} sessions, {total(after, 'prompts')} prompts, {total(after, 'closes')} /mimi-close runs",
        f"  tokens processed: {total(after, 'input'):,} input ({total(after, 'cached'):,} of them cache reads), {total(after, 'output'):,} output",
        f"  spent loading memory: ~{autoload * len(after):,} tokens ({autoload:,} x {len(after)} sessions, today's size)",
    ]
    if len(before) >= MIN_SESSIONS and len(after) >= MIN_SESSIONS:
        rows = [("input tokens", "input"), ("tool calls", "tools"), ("searches", "searches")]
        out += ["", "  median per prompt     before     after"]
        out += [f"  {label:<18}{per_prompt(before, k):>10,.1f}{per_prompt(after, k):>10,.1f}" for label, k in rows]
        saved = (per_prompt(before, "input") - per_prompt(after, "input")) * total(after, "prompts")
        out.append(f"  estimated input tokens saved: {saved:,.0f} (median difference x prompts since adoption;"
                   " different tasks, so a trend, not a measurement)")
    else:
        out.append(f"  before/after comparison needs {MIN_SESSIONS} sessions on each side, have {len(before)} before and {len(after)} after")
    reads = sum((s["reads"] for s in after), Counter())
    opened = sum(bool(s["reads"]) for s in after)
    out += ["", "Memory use since adoption", f"  sessions that opened a memory file: {opened} of {len(after)}"]
    for rel in layer:
        if rel in ("CLAUDE.md", "STATE.md"):
            continue
        out.append(f"  {rel:<30} {f'read {reads[rel]}x' if reads[rel] else 'never read' + (', empty' if rel in empty else '')}")
    return "\n".join(out)


def selftest() -> None:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "CLAUDE.md").write_bytes(b"# Mine\r\n- Old note \xe2\x86\x92 `memory/external.md`\r\n")
        assert len(init(root)) == 5
        assert init(root) == []
        assert read(root / "CLAUDE.md").startswith("# Mine\n- Old note → `memory/external.md`\n")
        assert b"\r\n" in (root / "CLAUDE.md").read_bytes()
        assert check(root) == [], check(root)
        (root / "memory/db.md").write_text("quirk\n", encoding="utf-8")
        assert len(check(root)) == 2, check(root)
        (root / "memory/db.md").write_text("Last verified: 2026-13-45\n", encoding="utf-8")
        assert any("not a YYYY-MM-DD" in p for p in check(root))
        (root / "memory/db.md").unlink()
        (root / "ISSUES.md").write_text("# Issues\n## ISS-1 — x\nSymptom: boom\n```\n# comment\n```\nCause: y\n## ISS-2 — z\nSymptom: a\n", encoding="utf-8")
        assert "CLAUDE.md: index lines are stale, run index" in check(root)
        assert index(root) and "`ISSUES.md` (search the exact error text)\n" in read(root / "CLAUDE.md")
        assert check(root) == ["ISSUES.md: 'ISS-2 — z' needs Symptom: and Cause:"], check(root)
        (root / "ISSUES.md").write_text("# Issues\n", encoding="utf-8")
        assert index(root) and "(search the exact error text) — empty" in read(root / "CLAUDE.md")
        ext = root / "memory/external.md"
        ext.write_text(read(ext) + "\n## stripe sends duplicate webhooks\n", encoding="utf-8")
        assert check(root) == ["CLAUDE.md: index lines are stale, run index"], check(root)
        assert index(root) and "— contains: stripe sends duplicate webhooks" in read(root / "CLAUDE.md")
        assert "- Old note → `memory/external.md`\n" in read(root / "CLAUDE.md")
        assert not index(root)
        (root / "STATE.md").write_text("x\n" * 61, encoding="utf-8")
        assert check(root) == ["STATE.md: 61 lines, cap 60"], check(root)
        (root / "STATE.md").write_text("<<<<<<< HEAD\nx\n", encoding="utf-8")
        assert check(root) == ["STATE.md: contains git conflict markers"], check(root)
        saved_env = os.environ.get("CLAUDE_CONFIG_DIR")
        os.environ["CLAUDE_CONFIG_DIR"] = str(root / "cfg")
        try:
            tdir = transcript_dir(root)
            tdir.mkdir(parents=True)
            usage = {"input_tokens": 10, "cache_read_input_tokens": 90, "output_tokens": 5}
            grep = {"type": "tool_use", "id": "t1", "name": "Grep", "input": {}}
            init_cmd = {"type": "tool_use", "id": "t2", "name": "Bash", "input": {"command": "python memlayer.py init ."}}
            a = [
                {"type": "user", "timestamp": "2026-01-01T00:00:00Z", "message": {"content": "fix the bug"}},
                {"type": "assistant", "message": {"id": "m1", "usage": usage, "content": [grep]}},
                {"type": "assistant", "message": {"id": "m1", "usage": usage, "content": [init_cmd]}},
            ]
            read_mem = {"type": "tool_use", "id": "t3", "name": "Read", "input": {"file_path": str(root / "memory/external.md")}}
            b = [
                {"type": "user", "timestamp": "2026-01-02T00:00:00Z", "message": {"content": "<command-name>/mimi-close</command-name>"}},
                {"type": "user", "message": {"content": "<local-command-stdout>x</local-command-stdout>"}},
                {"type": "assistant", "message": {"id": "m2", "usage": usage, "content": [read_mem]}},
                {"type": "user", "message": {"content": [{"type": "tool_result", "content": "..."}]}},
                {"type": "user", "isSidechain": True, "message": {"content": "subagent prompt"}},
            ]
            for name, events in (("a", a), ("b", b)):
                (tdir / f"{name}.jsonl").write_text("\n".join(map(json.dumps, events)) + "\nnot json\n", encoding="utf-8")
            first, second = sessions(root)
            assert (first["input"], first["output"], first["tools"], first["searches"], first["init"], first["prompts"]) == (100, 5, 2, 1, True, 1), first
            assert (second["prompts"], second["closes"], dict(second["reads"])) == (1, 1, {"memory/external.md": 1}), second
            assert adopted(root, [first, second]) == first["start"]
            report = stats(root)
            assert "memory/external.md             read 1x" in report and "1 /mimi-close runs" in report, report
        finally:
            if saved_env is None:
                os.environ.pop("CLAUDE_CONFIG_DIR")
            else:
                os.environ["CLAUDE_CONFIG_DIR"] = saved_env
    print("SELFTEST_OK")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    usage = "usage: memlayer.py init [dir] | index [dir] | check [dir] | stats [dir] | selftest"
    if len(sys.argv) < 2 or sys.argv[1] not in ("init", "index", "check", "stats", "selftest"):
        print(usage)
        return 2
    if sys.argv[1] == "selftest":
        selftest()
        return 0
    root = Path(sys.argv[2] if len(sys.argv) > 2 else ".").resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory")
        return 2
    try:
        if sys.argv[1] == "init":
            print("\n".join(init(root)) or "already initialised, nothing to do")
            return 0
        if sys.argv[1] == "index":
            result = index(root)
            if result is None:
                print("no memory-layer block in CLAUDE.md, run init first")
                return 1
            print("index lines updated" if result else "index already current")
            return 0
        if sys.argv[1] == "stats":
            print(stats(root))
            return 0
        problems = check(root)
    except (OSError, UnicodeDecodeError) as e:
        print(f"error: {e}")
        return 1
    print("\n".join(problems) or "memory layer clean")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
