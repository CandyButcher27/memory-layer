import re
import subprocess
import sys
from pathlib import Path

arm, ml = Path(sys.argv[1]), Path(sys.argv[2])
claude = arm / "CLAUDE.md"
s = claude.read_text(encoding="utf-8")
tpl = (ml.parent / "templates/CLAUDE-block.md").read_text(encoding="utf-8").replace("{memlayer}", ml.as_posix())
for prefix in ("Every file in", "- Fact the code"):
    line = next(l for l in tpl.splitlines() if l.startswith(prefix))
    s = re.sub(rf"^{re.escape(prefix)}.*$", lambda m: line, s, flags=re.M)
s = re.sub(r'python "[^"]*memlayer\.py"', f'python "{ml.as_posix()}"', s)
claude.write_text(s, encoding="utf-8")
subprocess.run([sys.executable, str(ml), "index", str(arm)], check=True)
