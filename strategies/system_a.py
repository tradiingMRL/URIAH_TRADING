from collections import deque
from dataclasses import dataclass

from contracts.messages import MarketFeatures
from contracts.state import MarketState
from contracts.signals import Signal


@dataclass
class BoxState:
    high: float
    low: float
    stable_count: int


class SystemA:
    """
    System A (Breakout v0):
    - Maintains a rolling Darvas-style box from last N prices.
    - Requires the box to be stable for K ticks before allowing breakout signals.
    - Emits Signal only (no execution).
    """

    def __init__(self, config: dict):
        cfg = config or {}
        self.lookback_n = int(cfg.get("lookback_n", 20))
        self.stability_k = int(cfg.get("stability_k", 5))
        self.buffer_atr_mult = float(cfg.get("buffer_atr_mult", 0.0))

        self._prices = deque(maxlen=max(2, self.lookback_n))
        self._box = None  # type: BoxState | None

    def _update_box(self) -> BoxState:
        hi = max(self._prices)
        lo = min(self._prices)

        if self._box is None:
            self._box = BoxState(high=hi, low=lo, stable_count=1)
            return self._box

        # If high/low unchanged, increment stability; otherwise reset.
        if hi == self._box.high and lo == self._box.low:
            self._box.stable_count += 1
        else:
            self._box = BoxState(high=hi, low=lo, stable_count=1)

        return self._box

    def decide(self, features: MarketFeatures, state: MarketState) -> Signal:
        # Append latest price
        self._prices.append(float(features.price))

        # Need enough data to form a box
        if len(self._prices) < self._prices.maxlen:
            return Signal(
                timestamp=features.timestamp,
                instrument=features.instrument,
                strategy="SystemA",
                action="HOLD",
                strength=0.0,
                reason=f"system_a_warmup_{len(self._prices)}/{self._prices.maxlen}",
                tag="warmup",
            )

        box = self._update_box()

        # Require stability before breakout
        if box.stable_count < self.stability_k:
            return Signal(
                timestamp=features.timestamp,
                instrument=features.instrument,
                strategy="SystemA",
                action="HOLD",
                strength=0.0,
                reason=f"system_a_box_unstable_{box.stable_count}/{self.stability_k}",
                tag="box",
            )

        buffer = float(features.atr_fast) * self.buffer_atr_mult

        # Breakout conditions
        if features.price > (box.high + buffer):
            return Signal(
                timestamp=features.timestamp,
                instrument=features.instrument,
                strategy="SystemA",
                action="ENTER_LONG",
                strength=1.0,
                reason=f"breakout_up_over_{box.high}",
                tag="breakout",
            )

        if features.price < (box.low - buffer):
            return Signal(
                timestamp=features.timestamp,
                instrument=features.instrument,
                strategy="SystemA",
                action="ENTER_SHORT",
                strength=1.0,
                reason=f"breakout_down_under_{box.low}",
                tag="breakout",
            )

        return Signal(
            timestamp=features.timestamp,
            instrument=features.instrument,
            strategy="SystemA",
            action="HOLD",
            strength=0.0,
            reason="system_a_no_breakout",
            tag="hold",
        )