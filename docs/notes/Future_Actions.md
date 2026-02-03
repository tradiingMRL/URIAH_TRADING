# Future Actions Register
URIAH_TRADING

## A4 — Safety Enforcement (Policy → Execution)
Goal: Enforce Connection_Safety_Policy_v1.0 in live execution.

- Implement hard rule: NOT SAFE → FORCE FLAT immediately, regardless of trade state.
- Source signals:
  - NT connection state changes (Primary + Price Feed)
  - Broker-enforced disconnect / authorization errors
- Enforcement rules:
  - No new entries if NOT SAFE
  - If NOT SAFE occurs post-entry → force flat + lockout
  - Lockout persists until manual clear (or future session reset rule)
- Logging:
  - Emit FORCE_FLAT + LOCKOUT_EVENT into trade_events
  - Emit detailed record into connection_events
- Test plan (paper):
  - Induce disconnect scenario(s)
  - Verify force flat triggers
  - Verify logs + SQLite rows + dedupe
  - Verify no auto-resume

## A5 — Daily + Weekly Summary Automation
Goal: No manual admin. Auto-generate operational notes and rollups.

- Daily:
  - Auto-create docs/notes/Daily_Summary_YYYY-MM-DD.md (AU date)
  - Pull counts + key events from SQLite:
    - trades taken/denied
    - lockouts
    - connection_events NOT SAFE
    - PnL summary once live data exists
- Weekly:
  - Auto-create/update docs/notes/Weekly_Plan_YYYY-WW.md
  - Summarise “what happened last week” + “actions for coming week”
- Git:
  - Script creates files + runs git add/commit/push safely (same as current workflow)

## A6 — Read-only Web Dashboard (iPad-friendly)
Goal: One-click access (desktop icon + browser) for monitoring and review.

- Web-based dashboard (read-only):
  - equity curve
  - trade table with drill-down (trade → gates → components)
  - connection health panel (SAFE/NOT SAFE history)
  - lockout / force-flat event timeline
- Access control:
  - Shareable with your daughter using login/password
  - Role = view-only (“look, no touching”)
- Deployment:
  - Run on VPS (Chicago) as a lightweight local web service
  - Optional reverse proxy + HTTPS later