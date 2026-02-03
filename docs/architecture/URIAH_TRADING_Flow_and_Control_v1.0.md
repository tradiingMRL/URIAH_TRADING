# URIAH_TRADING — Flow & Control (v1.0 — design locked)

## 0. System Boundary (authoritative)

```mermaid
flowchart LR
    A[Market Data Source<br/>NT8 / Replay / Feed] --> B[Python Orchestrator<br/>Governor + State Resolver]
    B --> C[MarketState Message Contract<br/>Single Source of Truth]
    C --> D[NT8 Execution Engine<br/>Orders + Local Safety]
    D --> E[Broker / Exchange]

flowchart TD

    %% =========
    %% INPUT
    %% =========
    IN[MarketFeatures<br/>(normalized features)] --> SG[Safety Gate]

    %% =========
    %% SAFETY
    %% =========
    SG -->|FAIL| HALT[MarketState = HALT<br/>permission = BLOCK<br/>reason = SAFETY]
    SG -->|PASS| VG[Volatility Gate<br/>(non-ATR as locked)]

    %% =========
    %% VOLATILITY
    %% =========
    VG -->|FAIL| CHAOS[MarketState = CHAOTIC<br/>permission = REDUCE/BLOCK<br/>reason = VOLATILITY]
    VG -->|PASS| HMM[HMM Regime Inference]

    %% =========
    %% REGIME
    %% =========
    HMM --> RS[Regime State<br/>TREND / MEAN_REVERSION / CHAOTIC<br/>+ confidence]

    %% =========
    %% EARLY EXIT (permission-only modifier)
    %% =========
    RS --> EE[Early Exit Engine<br/>(permission downgrade only)]
    EE -->|ACTIVE| PERMBLOCK[permission = BLOCK<br/>reason = EARLY_EXIT]
    EE -->|INACTIVE| PERMOK[permission = ALLOW<br/>reason = OK]

    %% =========
    %% OUTPUT
    %% =========
    PERMBLOCK --> OUT[Publish MarketState]
    PERMOK --> OUT
    CHAOS --> OUT
    HALT --> OUT

    OUT --> PUB[Publisher<br/>(Message Contract)]
    PUB --> NT8[NT8 Execution (edge)]
    OUT --> LOG[Event Log / Metrics / Dashboard Feed]

Authority & Ownership (who may decide what)

flowchart LR
    SG2[Safety Gate] -->|may set| P1[permission = BLOCK]
    VG2[Volatility Gate] -->|may set| P2[permission = REDUCE/BLOCK]
    HMM2[HMM Engine] -->|may set| R1[regime = TREND / MEAN_REVERSION / CHAOTIC]
    EE2[Early Exit] -->|may set| P3[permission downgrade only]


Rules (locked):
	•	Safety failure ⇒ HALT + BLOCK (absolute)
	•	Volatility failure ⇒ CHAOTIC with REDUCE/BLOCK (no trading preference)
	•	HMM decides regime only
	•	Early Exit can only reduce permission (never changes regime)
	•	NT8 may execute only when permission allows; NT8 does not infer regime


⸻

## 2a. Module Ownership Table (Authority Lock)

| Module | Owns Decisions About | Explicitly Not Allowed To Do |
|------|----------------------|------------------------------|
| **Market Feed** | Raw data ingestion, normalization | Infer regime, block trading |
| **Safety Gate** | Global safety state, HALT conditions | Infer regime, downgrade permission selectively |
| **Volatility Gate** | Volatility accept / reject, CHAOTIC state | Decide trade direction, force execution |
| **HMM Engine** | Market regime (TREND / MEAN_REVERSION / CHAOTIC) + confidence | Risk sizing, permission control, execution |
| **Early Exit Engine** | Permission downgrade (ALLOW → BLOCK) | Change regime, override safety |
| **Orchestrator** | Ordering of gates, state assembly | Strategy logic, order placement |
| **MarketState Contract** | Single source of truth for downstream systems | Carry hidden or derived state |
| **NT8 Execution Engine** | Order execution, local broker safety | Regime inference, volatility logic |
| **Dashboard / Logs** | Observation, metrics, replay | Influence live decisions |

### Authority Rules (non-negotiable)

- **Safety Gate is absolute**  
  If Safety fails → `HALT + permission = BLOCK`, no exceptions.

- **Volatility Gate constrains, not directs**  
  It may reduce or block participation but never imply bias.

- **HMM decides regime only**  
  It does not know about PnL, drawdown, or order state.

- **Early Exit only removes permission**  
  It never upgrades permission and never changes regime.

- **NT8 executes, it does not decide**  
  NT8 trusts the `MarketState` and enforces only mechanical safety.

- **Dashboards observe only**  
  No feedback loops into live decision paths.


3. Message Contract Path (no hidden coupling)

sequenceDiagram
    participant FEED as Market Feed
    participant ORCH as Python Orchestrator
    participant LOG as Event Logger / Dashboard
    participant NT8 as NT8 Execution

    FEED->>ORCH: MarketFeatures (normalized)
    ORCH->>ORCH: Safety -> Volatility -> HMM -> EarlyExit
    ORCH->>LOG: Append Event + MarketState
    ORCH->>NT8: Publish MarketState (contract)
    NT8->>NT8: Execute orders only if permission allows

4. Terminal States (fail-closed)
	•	HALT: safety fail → permission = BLOCK
	•	CHAOTIC: volatility fail or low-confidence regime → permission = REDUCE/BLOCK
	•	TREND / MEAN_REVERSION: normal operations → permission = ALLOW unless Early Exit blocks

⸻

5. Notes (implementation commitments)
	•	Python is governor + state publisher
	•	NT8 is execution edge
	•	Every MarketState emitted is logged (replayable, auditable)
	•	No module depends on who consumes it; only on contracts



