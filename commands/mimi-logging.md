---
description: Show what mimi costs and saves in this project, from its Claude Code session logs, and save the report under mimi/logs/. Covers memory size, tokens loaded every session, tokens and searches per prompt before and after adoption, and which memory files get read.
allowed-tools: Bash, Read
---

# /mimi-logging

Report mimi's usage in this project. The only file this writes is the report under `mimi/logs/`.

1. If `mimi/MIMI.md` does not exist, tell the user to run `/mimi-start` first and stop. Otherwise the
   script's path is on its `Find rot:` line. Call it `$ML`.
2. Run `python "$ML" stats .`. It prints the report and saves it as `mimi/logs/stats-<date>.txt`. Show the
   output unchanged, in a code block.
3. Below it, add at most four lines, and only for what applies:
   - If there is an `estimated input tokens saved` line, say that it compares medians across different
     tasks before and after adoption. It shows a trend, not a controlled measurement. The controlled
     numbers are in mimi's README.
   - A memory file marked `never read` after 10 or more sessions is a candidate to merge or delete. Name
     it. Do not delete it.
   - If more than 3,000 tokens load into every session, suggest trimming `mimi/STATE.md` or shortening
     headings.
   - If `/mimi-close` ran in far fewer sessions than there were sessions, the memory is not being kept
     up to date. Say so.
