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
DIR = "mimi"
MAP = f"{DIR}/MIMI.md"
STATE = f"{DIR}/STATE.md"
ISSUES = f"{DIR}/ISSUES.md"
DECISIONS = f"{DIR}/decisions.md"
POINTER = f"{START}\n@{MAP}\n{END}\n"
SEEDED = ("MIMI.md", "STATE.md", "ISSUES.md", "decisions.md", "memory/external.md")
CAPS = {MAP: 100, STATE: 60}
MEMORY_CAP = 150
AUTOLOAD_CAP = 16_000
STALE_DAYS = 90
VERIFIED = re.compile(r"Last verified:\s*(\S+)")
COMMENT = re.compile(r"<!--.*?-->", re.S)
FENCE = re.compile(r"^```.*?^```[^\n]*$", re.S | re.M)
INDEX_LINE = re.compile(r"^(- .*?→ `(mimi/memory/[^`]+\.md)`)(?: — (?:contains: .*|empty))?$", re.M)
TOP_LINE = re.compile(r"^(- .*?→ `(mimi/ISSUES\.md|mimi/decisions\.md)`.*?)(?: — empty)?$", re.M)
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


def memory_files(root: Path) -> list[str]:
    return sorted(p.relative_to(root).as_posix() for p in (root / DIR / "memory").rglob("*.md"))


def init(root: Path) -> list[str]:
    done = []
    for name in SEEDED:
        dst = root / DIR / name
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            save(dst, render(name))
            done.append(f"created {DIR}/{name}")
    ignore = root / DIR / ".gitignore"
    if not ignore.exists():
        save(ignore, "*\n")
        done.append(f"created {DIR}/.gitignore (git ignores {DIR}/; delete this file to share memory through git)")
    claude = root / "CLAUDE.md"
    text, eol = load(claude)
    if START not in text:
        sep = "\n\n" if text.strip() else ""
        save(claude, text.rstrip() + sep + POINTER, eol)
        done.append(f"added the {MAP} import to CLAUDE.md")
    index(root)
    return done


def indexed(root: Path, text: str) -> str:
    def fill(m: re.Match) -> str:
        body = COMMENT.sub("", read(root / m[2]))
        heads = HEADING.findall(body)
        if heads:
            return m[1] + f" — contains: {'; '.join(h.strip() for h in heads)}"
        return m[1] + (" — empty" if is_empty(body) else "")

    def mark(m: re.Match) -> str:
        return m[1] + (" — empty" if is_empty(read(root / m[2])) else "")

    return TOP_LINE.sub(mark, INDEX_LINE.sub(fill, text))


def index(root: Path) -> bool | None:
    path = root / MAP
    if not path.exists():
        return None
    text, eol = load(path)
    new = indexed(root, text)
    if new != text:
        save(path, new, eol)
    return new != text


def check(root: Path) -> list[str]:
    problems = []
    for name, cap in CAPS.items():
        p = root / name
        if not p.exists():
            problems.append(f"{name}: missing, run init")
        elif (n := len(read(p).splitlines())) > cap:
            problems.append(f"{name}: {n} lines, cap {cap}")
    if START not in read(root / "CLAUDE.md"):
        problems.append(f"CLAUDE.md: does not import {MAP}, so memory never loads; run init")
    mapped = read(root / MAP)
    refs = {m[2] for m in INDEX_LINE.finditer(mapped)}
    autoload = sum(len(read(root / n).encode("utf-8")) for n in ("CLAUDE.md", MAP, STATE))
    if autoload > AUTOLOAD_CAP:
        problems.append(f"CLAUDE.md + {MAP} + {STATE}: {autoload:,} bytes load into every session, cap {AUTOLOAD_CAP:,}; merge memory files or shorten headings")
    if mapped and indexed(root, mapped) != mapped:
        problems.append(f"{MAP}: index lines are stale, run index")
    for rel in memory_files(root):
        text = read(root / rel)
        if "/" in rel[len(f"{DIR}/memory/"):]:
            problems.append(f"{rel}: in a subfolder of {DIR}/memory/; works, but a flat folder is easier to scan")
        if (n := len(text.splitlines())) > MEMORY_CAP:
            problems.append(f"{rel}: {n} lines, cap {MEMORY_CAP}, split by topic")
        if rel not in refs:
            problems.append(f"{rel}: not in the {MAP} index, so it is never read")
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
            problems.append(f"{MAP}: points to {ref}, which does not exist")
    issues = FENCE.sub("", COMMENT.sub("", read(root / ISSUES)))
    for entry in re.split(r"^(?=#{1,6} )", issues, flags=re.M):
        m = ISSUE.match(entry)
        if m and ("Symptom:" not in entry or "Cause:" not in entry):
            problems.append(f"{ISSUES}: '{m[1].strip()}' needs Symptom: and Cause:")
    for rel in (MAP, STATE, ISSUES, DECISIONS, *memory_files(root)):
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
            if rel in (ISSUES, DECISIONS) or rel.startswith(f"{DIR}/memory/"):
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
    if not (root / MAP).exists():
        return f"no {MAP}, run /mimi-start first"
    layer = [n for n in (MAP, STATE, ISSUES, DECISIONS) if (root / n).exists()] + memory_files(root)
    texts = {rel: read(root / rel) for rel in layer}
    lines = sum(len(t.splitlines()) for t in texts.values())
    size = sum(len(t.encode("utf-8")) for t in texts.values())
    autoload = sum(len(read(root / n).encode("utf-8")) for n in ("CLAUDE.md", MAP, STATE)) // BYTES_PER_TOKEN
    heads = {rel: len(HEADING.findall(COMMENT.sub("", t))) for rel, t in texts.items()}
    traps = sum(n for rel, n in heads.items() if rel.startswith(f"{DIR}/memory/"))
    readable = [rel for rel in layer if rel not in (MAP, STATE)]
    empty = [rel for rel in readable if is_empty(texts[rel])]
    closed = re.search(r"Last updated:\s*(\d{4}-\d{2}-\d{2})", texts.get(STATE, ""))
    out = [
        f"mimi stats for {root}",
        "",
        "Memory",
        f"  {len(layer)} files, {lines} lines, {size / 1000:.1f} KB",
        f"  loaded into every session: CLAUDE.md + {MAP} + {STATE} ~ {autoload:,} tokens",
        f"  {heads.get(ISSUES, 0)} issues, {heads.get(DECISIONS, 0)} decisions, {traps} traps in {DIR}/memory/, {len(empty)} empty files",
        f"  {STATE} last updated: {closed[1] if closed else 'never'}",
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
    for rel in readable:
        out.append(f"  {rel:<35} {f'read {reads[rel]}x' if reads[rel] else 'never read' + (', empty' if rel in empty else '')}")
    return "\n".join(out)


def save_stats(root: Path, report: str) -> Path:
    path = root / DIR / "logs" / f"stats-{date.today().isoformat()}.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    save(path, report + "\n")
    return path


def selftest() -> None:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "CLAUDE.md").write_bytes(b"# Mine\r\n- Old note \xe2\x86\x92 `memory/external.md`\r\n")
        assert len(init(root)) == 7, init(root)
        assert init(root) == []
        assert read(root / "CLAUDE.md") == "# Mine\n- Old note → `memory/external.md`\n\n" + POINTER
        assert b"\r\n" in (root / "CLAUDE.md").read_bytes()
        assert read(root / DIR / ".gitignore") == "*\n"
        assert check(root) == [], check(root)
        (root / "mimi/memory/db.md").write_text("quirk\n", encoding="utf-8")
        assert len(check(root)) == 2, check(root)
        (root / "mimi/memory/db.md").write_text("Last verified: 2026-13-45\n", encoding="utf-8")
        assert any("not a YYYY-MM-DD" in p for p in check(root))
        (root / "mimi/memory/db.md").unlink()
        (root / ISSUES).write_text("# Issues\n## ISS-1 — x\nSymptom: boom\n```\n# comment\n```\nCause: y\n## ISS-2 — z\nSymptom: a\n", encoding="utf-8")
        assert f"{MAP}: index lines are stale, run index" in check(root)
        assert index(root) and "`mimi/ISSUES.md` (search the exact error text)\n" in read(root / MAP)
        assert check(root) == [f"{ISSUES}: 'ISS-2 — z' needs Symptom: and Cause:"], check(root)
        (root / ISSUES).write_text("# Issues\n", encoding="utf-8")
        assert index(root) and "(search the exact error text) — empty" in read(root / MAP)
        ext = root / "mimi/memory/external.md"
        ext.write_text(read(ext) + "\n## stripe sends duplicate webhooks\n", encoding="utf-8")
        assert check(root) == [f"{MAP}: index lines are stale, run index"], check(root)
        assert index(root) and "— contains: stripe sends duplicate webhooks" in read(root / MAP)
        assert "- Old note → `memory/external.md`\n" in read(root / "CLAUDE.md")
        assert not index(root)
        (root / STATE).write_text("x\n" * 61, encoding="utf-8")
        assert check(root) == [f"{STATE}: 61 lines, cap 60"], check(root)
        (root / STATE).write_text("<<<<<<< HEAD\nx\n", encoding="utf-8")
        assert check(root) == [f"{STATE}: contains git conflict markers"], check(root)
        (root / STATE).write_text("# State\n", encoding="utf-8")
        (root / "CLAUDE.md").write_text("# Mine\n", encoding="utf-8")
        assert check(root) == [f"CLAUDE.md: does not import {MAP}, so memory never loads; run init"], check(root)
        init(root)
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
            read_mem = {"type": "tool_use", "id": "t3", "name": "Read", "input": {"file_path": str(root / "mimi/memory/external.md")}}
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
            assert (second["prompts"], second["closes"], dict(second["reads"])) == (1, 1, {"mimi/memory/external.md": 1}), second
            assert adopted(root, [first, second]) == first["start"]
            report = stats(root)
            assert "mimi/memory/external.md             read 1x" in report and "1 /mimi-close runs" in report, report
            assert read(save_stats(root, report)).startswith("mimi stats for")
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
                print(f"no {MAP}, run init first")
                return 1
            print("index lines updated" if result else "index already current")
            return 0
        if sys.argv[1] == "stats":
            report = stats(root)
            print(report)
            if (root / MAP).exists():
                print(f"\nsaved to {save_stats(root, report).relative_to(root).as_posix()}")
            return 0
        problems = check(root)
    except (OSError, UnicodeDecodeError) as e:
        print(f"error: {e}")
        return 1
    print("\n".join(problems) or "memory layer clean")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
