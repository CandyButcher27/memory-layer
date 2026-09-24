# State
<!-- Now only. Overwritten every session. Finished work leaves. Cap 60 lines. -->

Goal: Git 2.56.0 release cycle; tree is at v2.56.0-rc2 (3bc0341126 "Git 2.56-rc2")

## Deployed
Not a deployed service. Latest tag: v2.56.0-rc2 (`git describe --tags`)

## Broken
- none known

## Open threads
- none

## Next 3
1. 
2. 
3. 

## Last session
<!-- Rewritten at every close, ~10 lines. Where the last session stopped, so the next one resumes cleanly. -->
Branch: master
Uncommitted: none (memory update committed)
Stopped at: infra corrected the self-hosted runner hard-kill limit from 45 to 60 minutes. Checked
`.github/workflows/*.yml` (no `timeout-minutes`) and `.gitlab-ci.yml` (`timeout: 2h`/`6h`, but
those jobs tag `saas-*` — GitLab SaaS runners, not our self-hosted fleet) and `ci/` (no script
sets its own timeout). Confirmed: no in-repo config needs to change; enforcement is at the
runner/infra level. Updated the 45-minute figure in memory/external.md and CLAUDE.md's index line.
Tried, failed: none
Resume with: normal work; add ISSUES/decisions entries as they come up.

Last updated: 2026-09-23
