#!/usr/bin/env bash
# Competitor pilot on cargo: D = mimi, M = claude-mem, L = claude-mem-lite.
# Each arm runs with its own HOME (plugins, hooks, data dirs) and its own logging proxy.
# Usage: bash pilot.sh setup | build | sessions | drain | recall | judge | tokens
set -u
W=$HOME/w
P=$W/pub
SHA=694054f34bcb04025b16d0eaf075038c0e58a15d
ARMS_ALL="D M L"
. $W/env.sh
port() { echo 84$(( $(printf '%d' "'$1") % 100 )); }
for a in $ARMS_ALL; do
  export ARM_${a}_HOME=$W/home/$a
  export ARM_${a}_ANTHROPIC_BASE_URL=http://127.0.0.1:$(port $a)
done
export ARM_D_EXTRA_TOOLS="Skill" ARM_M_EXTRA_TOOLS="Skill mcp__plugin_claude-mem_mcp-search" ARM_L_EXTRA_TOOLS="Skill mcp__mem-lite"
ADOPT="Follow the skill at $P/ml/skills/mimi/SKILL.md in Adopt mode on this project (the current directory). Its script is $P/ml/skills/mimi/memlayer.py. No user is available: a claim with nothing checkable behind it is dropped, not asked about. Do not delete any file. Finish when \`python3 $P/ml/skills/mimi/memlayer.py check .\` prints \"memory layer clean\", then print a short report."
mark() { python3 -c "import json,sys,time;p='$W/phases.json';d=json.load(open(p)) if __import__('os').path.exists(p) else {};i=int(sys.argv[1]);r=d.setdefault('$1',[0,0]);r[i]=r[i] if i==0 and r[0] else time.time();json.dump(d,open(p,'w'))" "$2"; }

case "$1" in
setup)
  [ -d $W/src ] || git clone -q https://github.com/rust-lang/cargo $W/src
  git -C $W/src checkout -q $SHA
  mkdir -p $W/wr $W/home $W/snap
  for a in $ARMS_ALL; do
    [ -d $W/wr/$a ] || cp -r $W/src $W/wr/$a
    mkdir -p $W/home/$a
    pgrep -f "proxy.py $(port $a)" >/dev/null || (nohup python3 $P/proxy.py $(port $a) $W/proxy_$a.jsonl >/dev/null 2>&1 < /dev/null &)
  done
  ;;
build)
  mark build 0
  (cd $W/wr/D && HOME=$W/home/D ANTHROPIC_BASE_URL=http://127.0.0.1:$(port D) claude -p "$ADOPT" --model opus     --output-format stream-json --verbose --allowedTools "Read Write Edit Grep Glob Bash"     --disallowedTools "Agent Workflow WebFetch WebSearch" < /dev/null > $P/build_D.jsonl)
  python3 $P/ml/skills/mimi/memlayer.py check $W/wr/D
  mark build 1
  ;;
sessions)
  for a in $ARMS_ALL; do [ -d $W/snap/$a ] || cp -r $W/wr/$a $W/snap/$a; done
  mark write 0
  cd $P && MODEL=sonnet ARMS=DML TASKS=${TASKS:-sessions.json} RESULTS=results_sessions python3 run.py session $W/wr
  mark write 1
  ;;
drain)
  mark drain 0
  # wait until no arm has written a proxy row or a worker transcript for 3 minutes (cap 30 minutes)
  for _ in $(seq 60); do
    newest=$(find $W/proxy_*.jsonl $W/home/*/.claude/projects -type f -newermt '-3 minutes' 2>/dev/null | head -1)
    [ -z "$newest" ] && break
    sleep 30
  done
  mark drain 1
  ;;
recall)
  mark recall 0
  cd $P && MODEL=sonnet ARMS=DML TASKS=recall.json RESULTS=results_recall python3 run.py run $W/wr all 3 3
  mark recall 1
  ;;
judge)
  cd $P && ARMS=DML TASKS=recall.json RESULTS=results_recall python3 run.py judge2 $W/wr > judge2_recall.txt
  ARMS=DML TASKS=recall.json RESULTS=results_recall python3 run.py report > report_recall.txt
  python3 hygiene.py $W/wr $W/snap > hygiene_out.txt
  ;;
tokens)
  for a in $ARMS_ALL; do python3 $P/tokens.py $W/home/$a $W/proxy_$a.jsonl $W/phases.json > $P/tokens_$a.json 2> $P/tokens_$a.txt; done
  ;;
esac
