# router/strategy_router.py

from contracts.enums import MarketRegime, TradePermission
from contracts.messages import MarketFeatures
from contracts.signals import Signal
from contracts.state import MarketState

# SystemA now uses on_bar(bar, position_state) and its own internal Action/PositionState/Bar
from strategies.system_a import SystemA
from strategies.system_a import Bar as SystemABar
from strategies.system_a import PositionState as SysAPositionState

from strategies.system_b import SystemB


class StrategyRouter:
    """
    Routes to System A/B based on MarketState.
    - If permission != ALLOW => always HOLD (control plane veto).
    - TREND => System A (Darvas Box Breakout)
    - MEAN_REVERSION => System B
    - else => HOLD
    """

    def __init__(self, config: dict | None = None):
        # Safe defaults even if init() is never called
        self.config: dict = {}
        self.sys_a: SystemA | None = None
        self.sys_b: SystemB | None = None

        # If caller provides config at construction time, initialize immediately
        if config is not None:
            self.init(config)

    def init(self, config: dict):
        """
        Initializes the router and its strategies.
        Your orchestrator may call this explicitly.
        """
        self.config = config or {}

        # Global EVT config (shared defaults)
        evt_cfg = (self.config or {}).get("evt", {})

        # -----------------------------
        # System A config (Darvas)
        # -----------------------------
        sys_a_cfg = dict((self.config or {}).get("system_a", {}))
        sys_a_cfg["evt"] = evt_cfg  # kept for future even if SystemA doesn't use it yet

        # SystemA signature:
        #   SystemA(lookback=20, min_width=5, expiry_bars=60, strategy_name="SystemA")
        lookback = int(sys_a_cfg.get("lookback", 20))
        min_width = int(sys_a_cfg.get("min_width", 5))
        expiry_bars = int(sys_a_cfg.get("expiry_bars", 60))

        self.sys_a = SystemA(
            lookback=lookback,
            min_width=min_width,
            expiry_bars=expiry_bars,
            strategy_name="SystemA",
        )

        # -----------------------------
        # System B config (unchanged)
        # -----------------------------
        sys_b_cfg = dict((self.config or {}).get("system_b", {}))
        sys_b_cfg["evt"] = evt_cfg
        self.sys_b = SystemB(sys_b_cfg)

    def route(self, features: MarketFeatures, state: MarketState) -> Signal:
        # Defensive: ensure initialized (common mistake when using .init pattern)
        if self.sys_a is None or self.sys_b is None:
            return Signal(
                timestamp=features.timestamp,
                instrument=features.instrument,
                strategy="Router",
                action="HOLD",
                strength=0.0,
                reason="router_not_initialized_call_init_first",
                tag="veto",
            )

        # Control-plane veto: if permission is blocked, nothing else runs
        if state.permission != TradePermission.ALLOW:
            return Signal(
                timestamp=features.timestamp,
                instrument=features.instrument,
                strategy="Router",
                action="HOLD",
                strength=0.0,
                reason=f"router_veto_permission_{state.permission.value}",
                tag="veto",
            )

        # TREND -> System A (Darvas)
        if state.regime == MarketRegime.TREND:
            # Prefer OHLC if available; otherwise fall back to price as close/high/low.
            price = getattr(features, "price", None)
            high = getattr(features, "high", None)
            low = getattr(features, "low", None)
            close = getattr(features, "close", None)

            if close is None:
                close = price
            if high is None:
                high = close
            if low is None:
                low = close

            # Defensive: if still None, we cannot run SystemA safely
            if close is None:
                return Signal(
                    timestamp=features.timestamp,
                    instrument=features.instrument,
                    strategy="Router",
                    action="HOLD",
                    strength=0.0,
                    reason="router_system_a_missing_price_or_close",
                    tag="veto",
                )

            bar_a = SystemABar(high=float(high), low=float(low), close=float(close))

            # Position state mapping for one-trade-at-a-time gating
            ps_raw = getattr(state, "position_state", None)
            ps = self._map_position_state(ps_raw)

            sig_a = self.sys_a.on_bar(bar_a, ps)

            # Map SystemA's signal to contracts.signals.Signal
            action_value = sig_a.action.value if hasattr(sig_a.action, "value") else str(sig_a.action)

            return Signal(
                timestamp=features.timestamp,
                instrument=features.instrument,
                strategy=sig_a.strategy,
                action=action_value,
                strength=float(sig_a.strength),
                reason=str(sig_a.reason),
                tag=str(sig_a.tag),
            )

        # MEAN_REVERSION -> System B (unchanged)
        if state.regime == MarketRegime.MEAN_REVERSION:
            return self.sys_b.decide(features, state)

        # No route
        return Signal(
            timestamp=features.timestamp,
            instrument=features.instrument,
            strategy="Router",
            action="HOLD",
            strength=0.0,
            reason=f"router_no_route_{state.regime.value}",
            tag="no_route",
        )

    @staticmethod
    def _map_position_state(ps_raw) -> SysAPositionState:
        """
        Map whatever the rest of your system stores into SystemA's PositionState enum.
        If you haven't implemented position states in MarketState yet, this defaults to FLAT.
        """
        if ps_raw is None:
            return SysAPositionState.FLAT

        # If it's already the correct enum, return it
        if isinstance(ps_raw, SysAPositionState):
            return ps_raw

        # If it's another enum or an object with .value, normalize to string
        if hasattr(ps_raw, "value"):
            ps_raw = ps_raw.value

        # Normalize common strings
        s = str(ps_raw).strip().upper()

        if s in ("FLAT", "NONE", "NO_POSITION"):
            return SysAPositionState.FLAT
        if s in ("LONG",):
            return SysAPositionState.LONG
        if s in ("SHORT",):
            return SysAPositionState.SHORT
        if s in ("PENDING_ENTRY_LONG", "PENDING_LONG", "ENTRY_LONG_PENDING"):
            return SysAPositionState.PENDING_ENTRY_LONG
        if s in ("PENDING_ENTRY_SHORT", "PENDING_SHORT", "ENTRY_SHORT_PENDING"):
            return SysAPositionState.PENDING_ENTRY_SHORT

        # Default safe fallback
        return SysAPositionState.FLAT