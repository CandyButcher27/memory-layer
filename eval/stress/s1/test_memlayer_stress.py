import os
import re
import stat
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
ML_DIR = REPO / "skills" / "mimi"
sys.path.insert(0, str(ML_DIR))
import memlayer  # noqa: E402

ML = ML_DIR / "memlayer.py"
TODAY = date.today().isoformat()
EXT_LINE = "→ `mimi/memory/external.md`"
MAP = "mimi/MIMI.md"


def cli(*args, env=None):
    base = {k: v for k, v in os.environ.items() if k not in ("PYTHONUTF8", "PYTHONIOENCODING")}
    r = subprocess.run([sys.executable, str(ML), *map(str, args)], capture_output=True, env=env or base)
    return r.returncode, r.stdout.decode("utf-8", "replace") + r.stderr.decode("utf-8", "replace")


def snapshot(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def project(tmp_path: Path) -> Path:
    root = tmp_path / "proj"
    root.mkdir()
    memlayer.init(root)
    return root


def add_memory(root: Path, name: str, body: str, when: str = "When testing") -> None:
    p = root / "mimi" / "memory" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"# {name}\nLast verified: {TODAY}\n{body}", encoding="utf-8")
    mapped = root / MAP
    text = mapped.read_text(encoding="utf-8")
    line = next(l for l in text.splitlines() if EXT_LINE in l)
    mapped.write_text(text.replace(line, f"{line}\n- {when} → `mimi/memory/{name}`", 1), encoding="utf-8")


def index_line(root: Path, name: str) -> str:
    return next(l for l in (root / MAP).read_text(encoding="utf-8").splitlines() if f"`mimi/memory/{name}`" in l)


def test_s1_01_init_and_index_idempotent(tmp_path):
    root = tmp_path / "p"
    root.mkdir()
    rc, out = cli("init", root)
    assert rc == 0 and "created" in out
    s1 = snapshot(root)
    rc, out = cli("init", root)
    assert rc == 0 and "nothing to do" in out
    assert snapshot(root) == s1
    ext = root / "mimi/memory/external.md"
    ext.write_text(ext.read_text(encoding="utf-8") + "\n## stripe sends duplicate webhooks\n", encoding="utf-8")
    rc, out = cli("index", root)
    assert "index lines updated" in out
    s2 = snapshot(root)
    rc, out = cli("index", root)
    assert rc == 0 and "already current" in out
    assert snapshot(root) == s2


@pytest.mark.parametrize("variant", ["crlf_bom", "lf_no_bom"])
def test_s1_02_existing_claude_md_prose_preserved(tmp_path, variant):
    root = tmp_path / "p"
    root.mkdir()
    nl = b"\r\n" if variant == "crlf_bom" else b"\n"
    bom = b"\xef\xbb\xbf" if variant == "crlf_bom" else b""
    prose = bom + nl.join(["# My project".encode(), "Keep this — exactly.".encode("utf-8"), b"- rule one", b""])
    (root / "CLAUDE.md").write_bytes(prose)
    rc, out = cli("init", root)
    assert rc == 0 and "Traceback" not in out
    new = (root / "CLAUDE.md").read_bytes()
    assert new.startswith(prose), new[: len(prose) + 20]
    assert new.count(memlayer.START.encode()) == 1
    cli("init", root)
    assert (root / "CLAUDE.md").read_bytes().count(memlayer.START.encode()) == 1


def test_s1_03_crlf_memory_file_headings(tmp_path):
    root = project(tmp_path)
    add_memory(root, "db.md", "")
    (root / "mimi/memory/db.md").write_bytes(
        f"# DB\r\nLast verified: {TODAY}\r\n## alpha trap\r\ntext\r\n### beta trap\r\n".encode())
    assert memlayer.index(root)
    raw = (root / MAP).read_bytes()
    line = next(l for l in re.split(rb"\r?\n", raw) if b"`mimi/memory/db.md`" in l)
    assert line.endswith(b"contains: alpha trap; beta trap"), line
    assert b"\r" not in line


HEADS = [
    "`KeyError: 'id'` in `db.py`",
    "retry → backoff loop",
    "deploy — prod only",
    "stripe — contains: duplicate events",
    "build fails 🚀 on arm64",
    "日本語の見出し",
    "Ошибка кодировки",
]


@pytest.mark.parametrize("head", HEADS)
def test_s1_04_unusual_headings_idempotent(tmp_path, head):
    root = project(tmp_path)
    add_memory(root, "x.md", f"## {head}\n## second trap\n")
    assert memlayer.index(root)
    first = (root / MAP).read_bytes()
    assert index_line(root, "x.md") == f"- When testing → `mimi/memory/x.md` — contains: {head}; second trap"
    assert not memlayer.index(root)
    assert (root / MAP).read_bytes() == first


def test_s1_04b_heading_with_memory_path_keeps_check_clean(tmp_path):
    root = project(tmp_path)
    add_memory(root, "x.md", "## moved from `mimi/memory/old.md`\n")
    assert memlayer.check(root) == [f"{MAP}: index lines are stale, run index"]
    memlayer.index(root)
    assert memlayer.check(root) == [], memlayer.check(root)


@pytest.mark.parametrize("name", ["My Notes.md", "DB.md", "api.v2.notes.md"])
def test_s1_05_odd_file_names_indexed_or_reported(tmp_path, name):
    root = project(tmp_path)
    add_memory(root, name, "## odd name trap\n")
    memlayer.index(root)
    indexed = "contains: odd name trap" in index_line(root, name)
    reported = any(name in p for p in memlayer.check(root))
    assert indexed or reported, f"indexed={indexed} check={memlayer.check(root)}"


def test_s1_06_nested_memory_file(tmp_path):
    root = project(tmp_path)
    add_memory(root, "sub/x.md", "## nested trap\n")
    memlayer.index(root)
    rc, out = cli("check", root)
    assert "Traceback" not in out
    docs = " ".join((ML_DIR / f).read_text(encoding="utf-8") for f in ("SKILL.md", "../../AGENTS.md", "templates/MIMI.md"))
    documented = re.search(r"nested|subdirector|subfolder|sub-folder", docs, re.I)
    assert "sub/x.md" in out or documented, out


def test_s1_07_two_index_lines_same_file(tmp_path):
    root = project(tmp_path)
    add_memory(root, "x.md", "## shared trap\n", when="When A")
    mapped = root / MAP
    text = mapped.read_text(encoding="utf-8")
    mapped.write_text(text.replace("- When A → `mimi/memory/x.md`", "- When A → `mimi/memory/x.md`\n- When B → `mimi/memory/x.md`"), encoding="utf-8")
    memlayer.index(root)
    lines = [l for l in mapped.read_text(encoding="utf-8").splitlines() if "`mimi/memory/x.md`" in l]
    assert lines == ["- When A → `mimi/memory/x.md` — contains: shared trap", "- When B → `mimi/memory/x.md` — contains: shared trap"]


def test_s1_08_index_shaped_prose_outside_block_untouched(tmp_path):
    root = tmp_path / "p"
    root.mkdir()
    prose = "# Mine\n- Old note → `mimi/memory/external.md`\n"
    (root / "CLAUDE.md").write_text(prose, encoding="utf-8")
    memlayer.init(root)
    ext = root / "mimi/memory/external.md"
    ext.write_text(ext.read_text(encoding="utf-8") + "\n## a trap\n", encoding="utf-8")
    memlayer.index(root)
    text = (root / "CLAUDE.md").read_text(encoding="utf-8")
    assert text.startswith(prose), text[:200]


@pytest.mark.parametrize("dates", [["2026-13-45"], ["2099-01-01"], [TODAY, "2020-01-01"]], ids=["invalid", "future", "two"])
def test_s1_09_bad_last_verified(tmp_path, dates):
    root = project(tmp_path)
    add_memory(root, "x.md", "")
    (root / "mimi/memory/x.md").write_text("# x\n" + "".join(f"Last verified: {d}\n" for d in dates), encoding="utf-8")
    rc, out = cli("check", root)
    assert "Traceback" not in out, out
    assert rc == 1 and "mimi/memory/x.md" in out, out


def test_s1_10_issues_mixed_formats(tmp_path):
    root = project(tmp_path)
    (root / "mimi/ISSUES.md").write_text(
        "# Issues\n"
        "## ISS-1 — complete\nSymptom: boom\nCause: x\nFix: abc123\n"
        "## ISS-2 — missing cause\nSymptom: y\n"
        "## ISS-3 — complete with fenced repro\nSymptom: script fails\n```bash\n# run with debug\n./x.sh\n```\nCause: CRLF\n"
        "### ISS-4 — h3 variant complete\nSymptom: a\nCause: b\n"
        "## ISS-5: colon style missing fields\nFix: none\n"
        "## Bug: non-template heading\nwhatever\n"
        "## ISS-6 — bold fields\n**Symptom:** a\n**Cause:** b\n",
        encoding="utf-8")
    flagged = [p for p in memlayer.check(root) if p.startswith("mimi/ISSUES.md")]
    assert flagged == [
        "mimi/ISSUES.md: 'ISS-2 — missing cause' needs Symptom: and Cause:",
        "mimi/ISSUES.md: 'ISS-5: colon style missing fields' needs Symptom: and Cause:",
    ], flagged


def test_s1_11_scale(tmp_path, capsys):
    root = project(tmp_path)
    for i in range(40):
        body = "".join(f"## topic{i:02d} trap {j:02d}: `SomeError` when calling service endpoint\nfact\n" for j in range(15))
        add_memory(root, f"topic-{i:02d}.md", body, when=f"Touching subsystem {i:02d}")
    t = time.perf_counter()
    rc, out = cli("index", root)
    elapsed = time.perf_counter() - t
    claude = root / MAP
    state = root / "mimi/STATE.md"
    with capsys.disabled():
        print(f"\nS1.11 index CLI {elapsed:.3f}s; MIMI.md {claude.stat().st_size} B, "
              f"{len(claude.read_text(encoding='utf-8').splitlines())} lines; STATE.md {state.stat().st_size} B; "
              f"check={memlayer.check(root)}")
    assert rc == 0 and "updated" in out
    assert elapsed < 5


def test_s1_12_missing_readonly_empty(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    for cmd in ("index", "check"):
        rc, out = cli(cmd, empty)
        assert "Traceback" not in out, (cmd, out)
    no_mem = project(tmp_path)
    import shutil
    shutil.rmtree(no_mem / "mimi" / "memory")
    rc, out = cli("check", no_mem)
    assert "Traceback" not in out, out
    ro = tmp_path / "ro"
    ro.mkdir()
    (ro / "CLAUDE.md").write_text("# Mine\n", encoding="utf-8")
    os.chmod(ro / "CLAUDE.md", stat.S_IREAD)
    try:
        rc, out = cli("init", ro)
    finally:
        os.chmod(ro / "CLAUDE.md", stat.S_IREAD | stat.S_IWRITE)
    assert "Traceback" not in out, out


def test_s1_12b_readonly_index(tmp_path):
    root = project(tmp_path)
    ext = root / "mimi/memory/external.md"
    ext.write_text(ext.read_text(encoding="utf-8") + "\n## a trap\n", encoding="utf-8")
    os.chmod(root / MAP, stat.S_IREAD)
    try:
        rc, out = cli("index", root)
    finally:
        os.chmod(root / MAP, stat.S_IREAD | stat.S_IWRITE)
    assert "Traceback" not in out, out


def test_s1_13_path_with_spaces_and_non_ascii(tmp_path):
    root = tmp_path / "my proj ü 日本 — x"
    root.mkdir()
    rc, out = cli("init", root)
    assert rc == 0 and "created" in out, out
    ext = root / "mimi/memory/external.md"
    ext.write_text(ext.read_text(encoding="utf-8") + "\n## a trap\n", encoding="utf-8")
    rc, out = cli("index", root)
    assert rc == 0 and "updated" in out, out
    rc, out = cli("check", root)
    assert rc == 0 and "clean" in out, out


def test_s1_13b_non_ascii_names_printed_by_check(tmp_path):
    root = tmp_path / "日本 proj"
    root.mkdir()
    memlayer.init(root)
    (root / "mimi/memory/日本.md").write_text(f"Last verified: {TODAY}\n", encoding="utf-8")
    rc, out = cli("check", root)
    assert "Traceback" not in out, out
    assert rc == 1 and f"not in the {MAP} index" in out, out


def test_s4_1_conflict_markers_reported(tmp_path):
    root = project(tmp_path)
    (root / "mimi/STATE.md").write_text("# State\n<<<<<<< HEAD\nGoal: a\n=======\nGoal: b\n>>>>>>> other\n", encoding="utf-8")
    assert "mimi/STATE.md: contains git conflict markers" in memlayer.check(root)


def test_s4_2_autoload_byte_cap(tmp_path):
    root = project(tmp_path)
    for i in range(40):
        add_memory(root, f"t{i:02d}.md", "".join(f"## trap {j:02d}: `SomeError` when calling endpoint\n" for j in range(15)), when=f"Area {i:02d}")
    memlayer.index(root)
    assert any("load into every session" in p for p in memlayer.check(root))


def test_s4_3_renamed_heading_flags_stale_index(tmp_path):
    root = project(tmp_path)
    add_memory(root, "x.md", "## old name\n")
    memlayer.index(root)
    (root / "mimi/memory/x.md").write_text(f"# x\nLast verified: {TODAY}\n## new name\n", encoding="utf-8")
    assert memlayer.check(root) == [f"{MAP}: index lines are stale, run index"]


def test_script_path_is_not_machine_absolute(tmp_path):
    root = project(tmp_path)
    block = (root / MAP).read_text(encoding="utf-8")
    if Path(memlayer.__file__).resolve().is_relative_to(Path.home()):
        assert '"$HOME/' in block and str(Path.home()).replace("\\", "/") not in block


def test_empty_files_marked_in_index_until_they_hold_entries(tmp_path):
    root = project(tmp_path)
    block = (root / MAP).read_text(encoding="utf-8")
    assert "`mimi/decisions.md` — empty" in block and "`mimi/memory/external.md` — empty" in block
    (root / "mimi/decisions.md").write_text("# Decisions\n## DEC-1 — use uv\nWhy: speed\n", encoding="utf-8")
    ext = root / "mimi/memory/external.md"
    ext.write_text(ext.read_text(encoding="utf-8") + "\nThe staging bucket is read-only on Fridays.\n", encoding="utf-8")
    assert memlayer.check(root) == [f"{MAP}: index lines are stale, run index"]
    memlayer.index(root)
    block = (root / MAP).read_text(encoding="utf-8")
    assert "`mimi/decisions.md` — empty" not in block and "`mimi/memory/external.md` — empty" not in block
    assert memlayer.check(root) == []


def test_s1_14_check_without_init(tmp_path):
    root = tmp_path / "raw"
    root.mkdir()
    (root / "main.py").write_text("print(1)\n", encoding="utf-8")
    rc, out = cli("check", root)
    assert "Traceback" not in out
    assert rc == 1
    assert f"{MAP}: missing" in out and "mimi/STATE.md: missing" in out, out


def test_mimi_folder_is_git_ignored_and_imported(tmp_path):
    root = project(tmp_path)
    assert (root / "mimi/.gitignore").read_text(encoding="utf-8") == "*\n"
    (root / "mimi/.ignore").unlink()
    assert memlayer.check(root) == ["mimi/.ignore: missing, so agent search tools cannot see mimi/; run init"]
    memlayer.init(root)
    assert (root / "mimi/.ignore").read_text(encoding="utf-8") == "!*\n"
    assert f"@{MAP}" in (root / "CLAUDE.md").read_text(encoding="utf-8")
    if subprocess.run(["git", "init", "-q", str(root)]).returncode == 0:
        status = subprocess.run(["git", "status", "--short", "--untracked-files=all"], cwd=root, capture_output=True, text=True).stdout
        assert status.split() == ["??", "CLAUDE.md"], status
