# NT8 Safety Watcher Design v1.0
URIAH_TRADING

Purpose:
Implement Connection Safety Policy v1.0 in NinjaTrader 8 using an AddOn
that is independent of any trading strategy.

References:
- docs/specs/Connection_Safety_Policy_v1.0.md
- docs/specs/Connection_Safety_Signal_Map_v1.0.md
- docs/specs/Connection_Safety_Heartbeat_Check_v1.0.md

---

## Architecture

### Components
1) NT8 AddOn: `UriahSafetyWatcher`
   - Monitors connection + heartbeat freshness
   - Maintains safety state SAFE / NOT SAFE
   - Executes FORCE FLAT + LOCKOUT actions

2) Strategy (System A/B):
   - Must consult lockout flag before placing any entry orders
   - Must NOT implement its own connection safety logic

Safety logic lives only in the AddOn.

---

## Safety Inputs

### A) Rithmic / NT8 Connection State
Source:
- NinjaTrader connection status callbacks/events
- Connection name: "My Rithmic for NinjaTrader Brokerage" (configurable)

NOT SAFE if primary != Connected OR pricefeed != Connected
OR if hard-failure messages detected:
- "Disconnect enforced by broker or 2nd login"
- "not authorized"

### B) Controller Heartbeat Freshness (Option A)
File:
- data/live/health/controller_heartbeat.json

NOT SAFE if:
- missing/unreadable/parse failure OR
- age > 30 seconds

Evaluation frequency:
- On connection events AND
- Timer loop every 5 seconds while connected

---

## Outputs / Actions

### Force Flat (Immediate)
When SAFE -> NOT SAFE transition occurs:
1) Cancel all working orders (account-wide)
2) Flatten all open positions (account-wide)
3) Set LOCKOUT = true

### Lockout
- While LOCKOUT is true:
  - Block ALL new orders (entry only is sufficient if strategy is disciplined,
    but AddOn may also cancel any new working orders defensively)

### Manual Reset (v1.0)
- Lockout clears only by explicit user action:
  - UI button in AddOn panel (later) OR
  - Config flag file toggle (temporary) OR
  - NT8 parameter setting (later)

No auto-unlock in v1.0.

---

## Event Subscriptions (Design Targets)

AddOn should subscribe to:
- Connection status changes (primary + pricefeed)
- Order updates (to detect unexpected new orders during lockout)
- Execution updates (audit + ensure flatten succeeded)
- Timer (5-second loop for heartbeat check)

---

## Logging (Minimum)
On any SAFE->NOT SAFE transition:
- Write connection_events CSV row
- Insert into SQLite (via ingestion pipeline)
- Emit FORCE_FLAT trade_events if a position was open

---

## Non-Goals (v1.0)
- No retries
- No grace period
- No auto unlock
- No L2-based safety logic