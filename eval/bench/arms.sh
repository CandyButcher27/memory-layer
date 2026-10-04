#!/usr/bin/env bash
# Per-arm adapter. Called by bench.py with HOME, WR, ARM, MIMI_SRC, CPORT set for one arm.
# Usage: bash arms.sh install|up|down|drain|dump
set -u
act=$1
CMEM=claude-mem@13.28.0
AMEM=@agentmemory/agentmemory@0.9.29

quiet() {
  # background capture is done when nothing under HOME but heartbeats and logs has changed for 45 s (cap 15 min)
  for _ in $(seq 60); do
    [ -z "$(find "$HOME" -type f -newermt '-45 seconds' -not -path '*/node_modules/*' -not -path '*/.npm/*'       -not -name '*health*' -not -name '*.log' -not -name '*.pid' -not -name 'engine-state.json' 2>/dev/null | head -1)" ] && return 0
    sleep 15
  done
  echo "drain: still writing after 15 min"
}
stop_all() { pkill -f "$HOME/" || true; sleep 1; pkill -9 -f "$HOME/" || true; }
wait_url() { for _ in $(seq 60); do curl -sf "$1" > /dev/null && return 0; sleep 2; done; echo "not up: $1"; return 1; }
plugin() {
  (cd "$HOME" && claude plugin marketplace add "$1" && claude plugin install "$2") || return 1
  claude plugin list 2>&1 | tail -20
}
# exit 0 only when the sqlite query counts at least one row
has_rows() { python3 -c "import sqlite3,sys;c=sqlite3.connect('file:$1?mode=ro',uri=True);sys.exit(c.execute(sys.argv[1]).fetchone()[0]==0)" "$2"; }
dump_files() { find "$@" -type f 2>/dev/null | sort | while read -r f; do echo "===== $f"; head -c 20000 "$f"; echo; done; }
warm() {
  # some tools record nothing for the first session after install: run two outside the arm's project
  mkdir -p "$HOME/warm" && cd "$HOME/warm" || return 1
  for _ in 1 2; do claude -p "Reply with exactly: ok" --model haiku --max-turns 1 > /dev/null; done
  cd - > /dev/null
}

sm_config() {
  mkdir -p "$WR/.claude/.supermemory-claude"
  printf '{"repoContainerTag": "%s"%s}
' "$TAG" "${1:-}" > "$WR/.claude/.supermemory-claude/config.json"
}

case "$ARM:$act" in
# Supermemory keeps its store in the cloud, which a restore cannot reset: eval sessions capture nothing
S:evalmode) sm_config ', "signalExtraction": true, "signalKeywords": ["zz-bench-never-matches"]' ;;
*:evalmode) ;;
A:dump) echo "no memory" ;;
N:dump) dump_files "$HOME/.claude/projects" -path '*/memory/*' ;;
A:*|N:*) ;;

D:install|D0:install)
  # the released layout: four skills under ~/.claude/skills, /mimi-close is a skill
  mkdir -p "$HOME/.claude/skills"
  rsync -a --exclude=__pycache__ "$MIMI_SRC/skills/" "$HOME/.claude/skills/"
  echo "mimi from $MIMI_SRC: memlayer.py sha256 $(sha256sum "$HOME/.claude/skills/mimi/memlayer.py" | cut -c1-12)"
  ;;
D:dump|D0:dump) dump_files "$WR/mimi"; echo "===== CLAUDE.md"; cat "$WR/CLAUDE.md" 2>/dev/null ;;
D:*|D0:*) ;;

M:install)
  (cd "$HOME" && timeout 300 npx -y $CMEM install --provider claude)
  # the npx installer leaves a marketplace Claude Code cannot read ("cache-miss"); re-register it with the CLI
  (cd "$HOME" && claude plugin marketplace remove thedotmack; claude plugin marketplace add thedotmack/claude-mem && claude plugin install claude-mem@thedotmack)
  python3 - <<EOF
import json; p='$HOME/.claude-mem/settings.json'; d=json.load(open(p))
d['CLAUDE_MEM_LOG_LEVEL']='DEBUG'; d['CLAUDE_MEM_WORKER_PORT']='$CPORT'; json.dump(d,open(p,'w'),indent=2)
EOF
  (cd "$HOME" && npx -y $CMEM start) && wait_url "127.0.0.1:$CPORT/api/health" || exit 1
  warm && sleep 20
  python3 -c "import sqlite3;c=sqlite3.connect('file:$HOME/.claude-mem/claude-mem.db?mode=ro',uri=True);print('claude-mem sessions:',c.execute('select project,count(*) from sdk_sessions group by project').fetchall())"
  (cd "$HOME" && npx -y $CMEM stop); stop_all
  claude plugin list 2>&1 | tail -5
  ;;
M:up) (cd "$HOME" && npx -y $CMEM start > /dev/null 2>&1) && wait_url "127.0.0.1:$CPORT/api/health" ;;
M:down) (cd "$HOME" && timeout 60 npx -y $CMEM stop > /dev/null 2>&1); stop_all ;;
M:drain)
  quiet_n=0
  for _ in $(seq 90); do
    s=$(curl -s "127.0.0.1:$CPORT/api/processing-status")
    case "$s" in *'"isProcessing":false'*'"queueDepth":0'*) quiet_n=$((quiet_n + 1)) ;; *) quiet_n=0 ;; esac
    [ $quiet_n -ge 3 ] && break
    sleep 20
  done
  quiet
  ;;
M:dump) python3 -c "
import sqlite3;c=sqlite3.connect('file:$HOME/.claude-mem/claude-mem.db?mode=ro',uri=True)
for r in c.execute('select * from observations'): print(r)
for r in c.execute('select * from session_summaries'): print(r)" ;;
# claude-mem's observer may skip every event of a read-only session: check its observer ran and got a reply, not that it stored anything
M:captured) has_rows "$HOME/.claude-mem/claude-mem.db" "select count(*) from sdk_sessions where project='$(basename "$WR")' and memory_session_id is not null" || exit 1 ;;

G:install)
  bash "$0" up || exit 1
  plugin rohitg00/agentmemory agentmemory@agentmemory || exit 1
  warm && bash "$0" drain && bash "$0" down
  ;;
G:up)
  # agentmemory downloads iii-engine on first start and runs without it when the download fails
  test -x "$HOME/.agentmemory/bin/iii" || { echo "iii-engine missing in $HOME/.agentmemory/bin"; exit 1; }
  mkdir -p "$HOME/.agentmemory-data"
  (cd "$HOME" && CI=1 AGENTMEMORY_DATA_DIR="$HOME/.agentmemory-data" nohup npx -y $AMEM --data-dir "$HOME/.agentmemory-data" &) > "$HOME/agentmemory.log" 2>&1 < /dev/null
  wait_url "http://localhost:3111/agentmemory/livez"
  ;;
G:down) stop_all ;;
G:drain) quiet ;;
G:dump) dump_files "$HOME/.agentmemory" -name '*.md'; curl -s "http://localhost:3111/agentmemory/health"; ls -laR "$HOME/.agentmemory-data" | head -40 ;;
# keyless observations carry no path, so look for a session started in the arm's repo that recorded an observation
G:captured) python3 - "$HOME/.agentmemory-data/state_store.db/mem%3Asessions.bin" "$WR" <<'EOF' || exit 1
import json, sys
d, _ = json.JSONDecoder().raw_decode(open(sys.argv[1], encoding="utf-8", errors="ignore").read())
sys.exit(not any(s.get("cwd") == sys.argv[2] and s.get("observationCount", 0) > 0 for s in d.values()))
EOF
  ;;

R:install)
  plugin Digital-Process-Tools/claude-marketplace remember@dpt-plugins || exit 1
  # Claude Code keeps CLAUDE_CODE_OAUTH_TOKEN out of hook processes, so remember's Haiku call needs its own token
  python3 -c 'import json,os; print(json.dumps({"oauth_token": os.environ["CLAUDE_CODE_OAUTH_TOKEN"]}))' | claude plugin configure remember@dpt-plugins --values-stdin || exit 1
  warm ;;
R:drain) quiet ;;
R:down) stop_all ;;
R:dump) dump_files "$WR/.remember" "$HOME/.remember" ;;
# remember's Haiku call may answer SKIP on a read-only session and write no now.md: a logged token count shows the call ran
R:captured) test -s "$WR/.remember/now.md" || grep -qs '\[tokens\]' "$WR"/.remember/logs/memory-*.log || exit 1 ;;
R:*) ;;

L:install) plugin sdsrss/claude-mem-lite claude-mem-lite@sdsrss || exit 1; warm ;;
L:drain) quiet ;;
L:down) stop_all ;;
L:dump) python3 -c "
import glob,sqlite3
for p in glob.glob('$HOME/.claude-mem-lite/*.db'):
    c=sqlite3.connect(f'file:{p}?mode=ro',uri=True)
    for (t,) in c.execute(\"select name from sqlite_master where type='table' and name not like '%fts%'\"):
        rows=c.execute(f'select * from {t}').fetchall()
        print('=====',p,t,len(rows))
        for r in rows[:200]: print(r)" ;;
L:captured) has_rows "$HOME/.claude-mem-lite/claude-mem-lite.db" "select count(*) from session_summaries where project like '%wr--$ARM'" || exit 1 ;;
L:*) ;;

K:install) plugin raiyanyahya/recall recall@recall || exit 1; warm ;;
K:drain) quiet ;;
K:down) stop_all ;;
K:dump) dump_files "$WR/.recall" ;;
K:captured) test -s "$WR/.recall/history.md" || exit 1 ;;
K:*) ;;

S:install) plugin supermemoryai/claude-supermemory supermemory@supermemory-plugins || exit 1; sm_config; warm ;;
S:drain) sleep 90; quiet ;;
S:down) stop_all ;;
S:dump) dump_files "$HOME/.supermemory-claude" "$WR/.claude/.supermemory-claude"; echo "store is in the Supermemory cloud, container $TAG" ;;
S:*) ;;

*) echo "unknown $ARM:$act"; exit 2 ;;
esac
exit 0
