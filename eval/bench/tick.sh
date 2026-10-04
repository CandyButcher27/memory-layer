#!/usr/bin/env bash
mkdir -p "$HOME/bench"
python3 "$(dirname "$0")/bench.py" tick >> "$HOME/bench/tick.log" 2>&1
