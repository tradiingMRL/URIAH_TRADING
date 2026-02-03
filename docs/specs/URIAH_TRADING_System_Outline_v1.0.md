URIAH_TRADING — System Outline v1.0
==================================

Purpose
-------
This document is the master outline (table of contents + governance) for the URIAH_TRADING system.
It is the single reference that points to all specs. It is NOT executable logic.

Key Principle: “Gates veto; systems decide.”
- HMM and Volatility gates never DIRECT trades.
- They may veto at entry.
- Mid-trade changes may be a WEIGHTING FACTOR only (never an automatic kill by themselves).

----------------------------------------------------------------

1) Repo Layout (high level)
---------------------------
docs/specs/   -> binding system specifications (versioned)
docs/notes/   -> daily summaries, weekly plans, operator notes (not binding)
tools/python/ -> analytics + ingestion + controller utilities
tools/sqlite/ -> schema + migrations
data/live/    -> runtime data only (never committed)

----------------------------------------------------------------

2) Trading Systems (Execution Modules)
--------------------------------------
System A: Breakout + continuation (fixed size, fixed orders)
System B: Mean reversion (requires stronger L2 emphasis at entry + stall)
(Only one position at a time across systems)

----------------------------------------------------------------

3) Global Gates (non-directive)
-------------------------------
3.1 Safety / Connectivity Gate (absolute override)
- If NOT SAFE: force-flat + lockout until manual reset
Specs:
- docs/specs/Connection_Safety_Policy_v1.0.md
- docs/specs/Connection_Safety_Signal_Map_v1.0.md

3.2 HMM Global State Gate (veto at entry only)
- States: CHOP / BREAKOUT_WINDOW / LATE_TREND
- Never directs trades; only veto at entry + post-entry weighting factor
Spec:
- docs/specs/HMM_Global_State_v1.0.md  (to be created)

3.3 Volatility Stats Gate (separate from HMM)
- Unrestrained volatility veto at entry
- Post-entry state changes are weighting factor only
Spec:
- docs/specs/Volatility_Gate_v1.0.md  (to be created)

----------------------------------------------------------------

4) Decision Tree (binding)
--------------------------
- Entry decision tree: gates -> system-specific rules -> order placement
- Management: kitbag weighting (early exit decisions)
- Exit: SL/TP fixed; early exit only by kitbag rules (never by HMM/Vol alone)
Spec:
- docs/specs/Decision_Tree_v1.0.md  (to be created)

----------------------------------------------------------------

5) Data & Observability
-----------------------
5.1 Logging schema (CSV + SQLite)
- docs/specs/Data_Logging_Schema_v1.1.md
- docs/specs/SQLite_Schema_v1.0.md
- tools/sqlite/schema_v1.0.sql

5.2 Ingestion
- tools/python/ingest_csv_to_sqlite.py
- connection_events ingested
- safety_events table + writer

----------------------------------------------------------------

6) Operator Portal (future direction)
-------------------------------------
Goal:
- Web-based dashboard (iPad friendly)
- Read-only shared access for Mimi (“look no touching”)
Spec / future actions:
- docs/notes/Future_Actions.md (A4/A5/A6 items + portal direction)

----------------------------------------------------------------

7) Open Items (to be written next)
----------------------------------
[ ] docs/specs/Decision_Tree_v1.0.md
[ ] docs/specs/Volatility_Gate_v1.0.md
[ ] docs/specs/HMM_Global_State_v1.0.md
[ ] docs/specs/Trade_Management_Kitbag_v1.0.md

Versioning
----------
This outline is v1.0. Changes require commit + message: "docs: update system outline vX.Y".