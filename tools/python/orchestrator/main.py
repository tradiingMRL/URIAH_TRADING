from __future__ import annotations

import time
from datetime import datetime, timezone

from tools.python.orchestrator.config import (
    LOG_FILE,
    LOG_LEVEL,
    HEARTBEAT_SEC,
    HEARTBEAT_FILE,
)
from tools.python.common.logging_setup import setup_logging
from tools.python.common.git_meta import git_metadata
from tools.python.common.heartbeat import HeartbeatWriter

from tools.python.common.market_state import MarketFeatures
from tools.python.orchestrator.state_builder import StateBuilder
from tools.python.orchestrator.router import Router


log = setup_logging(LOG_FILE, LOG_LEVEL)


def run() -> None:
    meta = git_metadata()
    log.info(f"ORCHESTRATOR START | git={meta}")

    hb = HeartbeatWriter(HEARTBEAT_FILE, service_name="orchestrator")

    # Core pipeline components
    state_builder = StateBuilder()
    router = Router()

    # Simple simulated market values (placeholder until real feed)
    price = 6000.0
    volume = 1000.0

    try:
        while True:
            now = datetime.now(timezone.utc)

            # 1) Heartbeat file update (machine-readable liveness)
            hb.beat(ok=True, note="loop_tick")

            # 2) Simulated feature snapshot (replace with real feed later)
            feats = MarketFeatures(
                timestamp=now,
                instrument="MES",
                price=price,
                volume=volume,
                atr_fast=1.0,
                atr_slow=2.0,
                vol_norm=0.50,
                velocity=0.10,
            )

            # 3) Build market state (gates + regime)
            state = state_builder.build(feats)

            # 4) Route decision (permission enforced here)
            signal = router.route(feats, state)

            # 5) Log one-line decision trace (audit-friendly)
            log.info(
                f"TICK instrument={feats.instrument} price={feats.price:.2f} "
                f"regime={state.regime.value} permission={state.permission.value} "
                f"vol_ok={state.volatility_ok} conf={state.confidence:.2f} "
                f"signal={signal.action} strat={signal.strategy} tag={signal.tag} "
                f"reason={signal.reason}"
            )

            time.sleep(HEARTBEAT_SEC)

    except KeyboardInterrupt:
        log.warning("ORCHESTRATOR INTERRUPTED BY USER")

    except Exception as e:
        hb.beat(ok=False, note=f"fatal:{type(e).__name__}")
        log.exception(f"FATAL ERROR: {e}")

    finally:
        log.info("ORCHESTRATOR SHUTDOWN CLEAN")


if __name__ == "__main__":
    run()