### 5.5 Communication Health & Fail-Safe (Authoritative)

NT8 must maintain a lightweight connection-health monitor for the Python orchestrator.

#### Health states
- `LINK_OK`
- `LINK_DEGRADED` (missed heartbeats or delayed responses)
- `LINK_LOST` (no contact beyond threshold)
- `LINK_CORRUPT` (invalid or inconsistent messages)

#### Hard rules
- If `LINK_DEGRADED|LOST|CORRUPT`:
  - NT8 must block all new entries (no trading without permission)
- If `LINK_CORRUPT`:
  - treat as Safety-critical immediately

#### In-position behaviour
- Catastrophic SL and fixed TP remain active regardless of link state.
- If `LINK_LOST` persists beyond a dwell threshold:
  - NT8 must fail-safe to flat using a marketable exit
  - log reason: `comms_fail_safe_flatten`

This behaviour must be deterministic and auditable.

NT8 must never silently trade an expired or unintended contract.

3.5 Reporting & Observability

NT8 must emit the following messages:
	•	ENTRY_INTENT
	•	FILL_REPORT (all fills: entry, exit, SL, TP)
	•	EXIT_ACK (early exit confirmation)
	•	ACTIVE_CONTRACT_STATUS (optional)

All reports must include:
	•	requested price
	•	filled price
	•	timestamps
	•	signed slippage
	•	instrument identity

⸻

3.5.1 Account & Position Reconciliation (Mandatory)

NT8 must periodically report truth snapshots so Python can verify alignment.

NT8 must emit:
	•	ACCOUNT_STATUS
	•	POSITION_STATUS

These snapshots allow Python to detect drift between:
	•	NT8 execution reality
	•	Python internal state and logs

If drift is detected, Python will:
	•	command an immediate flatten (EARLY_EXIT_NOW with trigger SAFETY), or
	•	enter LOCKOUT and require investigation

⸻

3.6 Local Fail-Safes

NT8 must locally enforce:
	•	one position at a time across System A and System B
	•	emergency flattening when instructed by Safety

These are last-resort protections, not decision logic.

⸻

4. Explicit Non-Responsibilities

NT8 must never:
	•	perform volatility classification
	•	run HMM or regime inference
	•	decide strategy compatibility
	•	evaluate trade health
	•	modify stops, targets, or sizing post-entry
	•	adjust trades based on PnL
	•	perform contract rollover logic autonomously

Any such logic in NT8 is a design violation.

⸻

5. Failure Behaviour (Authoritative)

5.1 Python Unavailable

If the Python orchestrator is unreachable:
	•	NT8 must block all new entries
	•	existing positions remain protected by catastrophic SL and TP

⸻

5.2 Permission Missing

If ENTRY_PERMISSION is not received:
	•	the entry must be abandoned
	•	no retries without a new ENTRY_INTENT

⸻

5.3 Early Exit Command

EARLY_EXIT_NOW overrides all local logic.
Exit execution must occur immediately.

⸻

5.4 Alignment Failures (Safety-Critical)

If Python detects mismatch between NT8-reported truth and Python state:

Position mismatch:
	•	immediate Safety escalation
	•	default action: flatten via EARLY_EXIT_NOW

Account balance or equity mismatch beyond tolerance:
	•	enter LOCKOUT
	•	investigate
	•	flatten if a live position exists

NT8 must continue reporting truth regardless of lockout state.

⸻

5.5 Communication Health & Fail-Safe (Authoritative)

NT8 must monitor communication health with Python.

Health states:
	•	LINK_OK
	•	LINK_DEGRADED
	•	LINK_LOST
	•	LINK_CORRUPT

Hard rules:
	•	if link is DEGRADED, LOST, or CORRUPT, block all new entries
	•	if link is CORRUPT, escalate immediately as Safety-critical

In-position behaviour:
	•	catastrophic SL and TP always remain active
	•	if LINK_LOST persists beyond dwell threshold, NT8 must fail-safe to flat using a marketable exit
	•	log reason: comms_fail_safe_flatten

This behaviour must be deterministic and auditable.

⸻

6. Design Invariants
	•	NT8 is stateless beyond its open position
	•	NT8 behaviour must be deterministic
	•	NT8 must be replaceable without changing system behaviour
	•	all intelligence lives outside the execution layer

⸻

7. Mental Model
	•	Python thinks
	•	NT8 executes
	•	logs explain what happened

⸻

8. Status

NT8 Execution Layer Design v1.0 — LOCKED

Any NT8 implementation must conform to this document.


