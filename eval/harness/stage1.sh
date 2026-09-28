#!/usr/bin/env bash
# Stage 1 (see eval/stage1/PREREG.md). Arms: A none, N built-in auto-memory, D mimi, M claude-mem.
# Usage: [ARMS_ALL="A N D M"] REPO=cargo|sqlite-utils|cargo-f2b|sqlite-utils-f2b|sqlite-utils-fix bash stage1.sh setup|build|sessions|drain|snapshot|eval|judge|tokens|state|restore <arm>
set -u
P=$HOME/w/pub
case "$REPO" in
  cargo*) URL=https://github.com/rust-lang/cargo; SHA=694054f34bcb04025b16d0eaf075038c0e58a15d ;;
  sqlite-utils*) URL=https://github.com/simonw/sqlite-utils; SHA=6bc1d33d583c54bd69fbdd2071117e2d38c354a1 ;;
esac
case "$REPO" in
  cargo) BASE=84 CPORT=37700 ;; sqlite-utils) BASE=85 CPORT=37700 ;;
  cargo-f2b) BASE=86 CPORT=37700 ;; sqlite-utils-f2b) BASE=87 CPORT=37701 ;; sqlite-utils-fix) BASE=88 CPORT=37702 ;;
esac
W=$HOME/w/$REPO
T=$P/stage1/$REPO
S=/tmp/snap-$REPO
ARMS_ALL=${ARMS_ALL:-A N D M}
has() { case " $ARMS_ALL " in *" $1 "*) return 0 ;; esac; return 1; }
CMEM=claude-mem@13.28.0
. $HOME/w/env.sh
port() { echo $BASE$(( $(printf '%d' "'$1") % 100 )); }
for a in $ARMS_ALL; do
  export ARM_${a}_HOME=$W/home/$a ARM_${a}_ANTHROPIC_BASE_URL=http://127.0.0.1:$(port $a) ARM_${a}_EXTRA_TOOLS=Skill
done
export ARM_A_CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 ARM_D_CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 ARM_M_CLAUDE_CODE_DISABLE_AUTO_MEMORY=1
export ARM_D_CLOSE_TURN=/mimi-close ARM_M_EXTRA_TOOLS="Skill mcp__plugin_claude-mem_mcp-search"
export EVAL_SUFFIX=$'\n\nDo not modify any file, and do not connect to the network. Keep the answer under 200 words and say what you relied on.'
export MODEL=sonnet ARMS=${ARMS_ALL// /}
mark() { python3 -c "import json,os,sys,time;p='$W/phases.json';d=json.load(open(p)) if os.path.exists(p) else {};i=int(sys.argv[1]);r=d.setdefault('$1',[0,0]);r[i]=r[i] if i==0 and r[0] else time.time();json.dump(d,open(p,'w'))" "$2"; }
cmem() { (cd $W && HOME=$W/home/M CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 timeout 180 npx -y $CMEM "$@" > /dev/null 2>&1); }
cmem_up() { for _ in $(seq 30); do curl -sf 127.0.0.1:$CPORT/api/health > /dev/null && return 0; sleep 2; done; echo "claude-mem worker not up"; return 1; }
# build outputs and tool runtimes are not memory state; they stay out of snapshots and restores
SKIP_HOME="--exclude=/.rustup/ --exclude=/.cargo/ --exclude=/.npm/ --exclude=/.bun/ --exclude=/.cache/ --exclude=/.local/ --exclude=node_modules/"
sync_home() { rsync -a --delete $SKIP_HOME --exclude '*.jsonl' --exclude 'logs/' "$1" "$2"; }
sync_wr() { rsync -a --delete --exclude=/target/ "$1" "$2"; }

case "$1" in
setup)
  mkdir -p $W/home $S/wr $S/home
  [ -d $W/src ] || git clone -q $URL $W/src
  git -C $W/src checkout -q $SHA
  for a in $ARMS_ALL; do
    [ -d $W/wr/$a ] || { mkdir -p $W/wr && cp -r $W/src $W/wr/$a; }
    mkdir -p $W/home/$a
    pgrep -f "proxy.py $(port $a)" > /dev/null || (nohup python3 $P/proxy.py $(port $a) $W/proxy_$a.jsonl > /dev/null 2>&1 < /dev/null &)
  done
  mkdir -p $W/home/D/.claude/skills && cp -r $P/ml/skills/mimi-* $W/home/D/.claude/skills/
  has M || exit 0
  cmem install --provider claude
  # the npx installer leaves a marketplace Claude Code cannot read ("cache-miss"); re-register it with the CLI
  (cd $W && export HOME=$W/home/M && claude plugin marketplace remove thedotmack && claude plugin marketplace add thedotmack/claude-mem && claude plugin install claude-mem@thedotmack) > /dev/null 2>&1
  python3 -c "import json;p='$W/home/M/.claude-mem/settings.json';d=json.load(open(p));d['CLAUDE_MEM_LOG_LEVEL']='DEBUG';d['CLAUDE_MEM_WORKER_PORT']='$CPORT';json.dump(d,open(p,'w'),indent=2)"
  cmem start && cmem_up
  # claude-mem's first session after install records nothing: warm it up outside the arm's project
  mkdir -p /tmp/warm-$REPO && (cd /tmp/warm-$REPO && HOME=$W/home/M CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 claude -p "Reply with exactly: ok" --model haiku --max-turns 1 > /dev/null)
  (cd /tmp/warm-$REPO && HOME=$W/home/M CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 claude -p "Reply with exactly: ok" --model haiku --max-turns 1 > /dev/null)
  sleep 20
  python3 -c "import sqlite3;c=sqlite3.connect('file:$W/home/M/.claude-mem/claude-mem.db?mode=ro',uri=True);print('claude-mem sessions:',c.execute('select project,count(*) from sdk_sessions group by project').fetchall())"
  ;;
build)
  mark build 0
  (cd $W/wr/D && HOME=$W/home/D ANTHROPIC_BASE_URL=http://127.0.0.1:$(port D) CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 claude -p "Follow the skill at $P/ml/SKILL.md in Adopt mode on this project (the current directory). Its script is $P/ml/memlayer.py. No user is available: a claim with nothing checkable behind it is dropped, not asked about. Do not delete any file. Finish when \`python3 $P/ml/memlayer.py check .\` prints \"memory layer clean\", then print a short report." --model opus --output-format stream-json --verbose --allowedTools "Read Write Edit Grep Glob Bash" --disallowedTools "Agent Workflow WebFetch WebSearch" < /dev/null > $W/build_D.jsonl)
  python3 $P/ml/memlayer.py check $W/wr/D
  mark build 1
  ;;
sessions)
  mark write 0
  cd $P && TASKS=$T/sessions.json RESULTS=$W/results_sessions python3 run.py session $W/wr
  mark write 1
  ;;
drain)
  has M || exit 0
  mark drain 0
  quiet=0
  for _ in $(seq 90); do
    s=$(curl -s 127.0.0.1:$CPORT/api/processing-status)
    case "$s" in *'"isProcessing":false'*'"queueDepth":0'*) quiet=$((quiet + 1)) ;; *) quiet=0 ;; esac
    [ $quiet -ge 3 ] && break
    sleep 20
  done
  echo "drain: $s"
  mark drain 1
  ;;
snapshot)
  has M && cmem stop
  mkdir -p $S/wr $S/home
  for a in $ARMS_ALL; do sync_wr $W/wr/$a/ $S/wr/$a/; sync_home $W/home/$a/ $S/home/$a/; done
  has M && { cmem start && cmem_up; }
  exit 0
  ;;
restore)
  a=$2
  [ "$a" = M ] && { pkill -f "worker-service.cjs hook"; cmem stop; }
  sync_wr $S/wr/$a/ $W/wr/$a/
  sync_home $S/home/$a/ $W/home/$a/
  [ "$a" = M ] && { cmem start && cmem_up; }
  exit 0
  ;;
eval)
  mark eval 0
  cd $P && export TASKS=$T/eval.json RESULTS=$W/results_eval PRE_RUN="bash $P/stage1.sh restore"
  ids() { python3 -c "import json;print(','.join(t['id'] for t in json.load(open('$T/eval.json')) if t['id'][0]=='$1'))"; }
  [ -n "$(ids R)" ] && python3 run.py run $W/wr $(ids R) 3 4
  [ -n "$(ids C)" ] && python3 run.py run $W/wr $(ids C) 5 4
  mark eval 1
  ;;
judge)
  cd $P && export TASKS=$T/eval.json RESULTS=$W/results_eval
  python3 run.py judge2 $W/wr > $W/judge2.txt
  python3 run.py report > $W/report.txt
  ;;
tokens)
  for a in $ARMS_ALL; do python3 $P/tokens.py $W/home/$a $W/proxy_$a.jsonl $W/phases.json > $W/tokens_$a.json 2> $W/tokens_$a.txt; done
  ;;
state)
  for a in $ARMS_ALL; do echo "== $a"; git -C $S/wr/$a status --short | head -20; git -C $S/wr/$a diff --stat | tail -3; done
  has N && echo "== N auto-memory" && find $S/home/N/.claude/projects -path '*memory*' -type f | sed "s|$W/||"
  has M && python3 -c "import sqlite3;c=sqlite3.connect('file:$S/home/M/.claude-mem/claude-mem.db?mode=ro',uri=True);print('== M observations',c.execute('select project,count(*) from observations group by project').fetchall());print('== M sessions',c.execute('select project,count(*) from sdk_sessions group by project').fetchall())"
  ;;
esac
