# system_a_darvas.py
# System A (Darvas Box Breakout) — locked defaults:
# - lookback = 20 bars (exclude current bar)
# - min box width = 5 consecutive CLOSES inside [bottom, top]
# - bounds use HIGH/LOW; breakout confirmation uses CLOSE
# - box expiry = 60 bars (stale reset)
# - one-trade-at-a-time: only emit ENTER_* when position_state == FLAT
#
# Drop-in design: you can delete your existing SystemA logic and paste this file.
# You only need to wire `SystemA.on_bar(...)` into your router loop.

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Deque, Optional, List
from collections import deque


# -----------------------------
# Common types (minimal, safe)
# -----------------------------

class Action(str, Enum):
    HOLD = "HOLD"
    ENTER_LONG = "ENTER_LONG"
    ENTER_SHORT = "ENTER_SHORT"


class PositionState(str, Enum):
    FLAT = "FLAT"
    PENDING_ENTRY_LONG = "PENDING_ENTRY_LONG"
    PENDING_ENTRY_SHORT = "PENDING_ENTRY_SHORT"
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass(frozen=True)
class Bar:
    """
    Minimal bar object. If your feed uses different names, adapt in the caller.
    """
    high: float
    low: float
    close: float


@dataclass(frozen=True)
class Signal:
    """
    Minimal signal object compatible with your logging style.
    Adjust fields if your project uses a different Signal shape.
    """
    strategy: str
    action: Action
    strength: float
    reason: str
    tag: str = "hold"


# -----------------------------
# Darvas box state
# -----------------------------

@dataclass
class DarvasBoxState:
    is_active: bool = False
    top: Optional[float] = None
    bottom: Optional[float] = None

    # Confirmation (formation)
    confirm_count: int = 0
    candidate_top: Optional[float] = None
    candidate_bottom: Optional[float] = None

    # When box was frozen (bar index)
    formed_at_index: Optional[int] = None

    def reset(self) -> None:
        self.is_active = False
        self.top = None
        self.bottom = None
        self.confirm_count = 0
        self.candidate_top = None
        self.candidate_bottom = None
        self.formed_at_index = None


# -----------------------------
# System A implementation
# -----------------------------

class SystemA:
    """
    Darvas Box Breakout System (long + short).
    - Forms box from rolling lookback window using high/low.
    - Requires min_width consecutive closes inside candidate box.
    - Freezes box on confirmation.
    - Breakout triggers on CLOSE beyond frozen top/bottom.
    - Expires stale frozen boxes after expiry_bars.
    - Emits entries only when position_state == FLAT (one trade at a time).
    """

    def __init__(
        self,
        lookback: int = 20,
        min_width: int = 5,
        expiry_bars: int = 60,
        strategy_name: str = "SystemA",
    ) -> None:
        if lookback < 5:
            raise ValueError("lookback should be >= 5 for meaningful structure")
        if min_width < 2:
            raise ValueError("min_width should be >= 2")
        if expiry_bars < min_width:
            raise ValueError("expiry_bars should be >= min_width")

        self.lookback = int(lookback)
        self.min_width = int(min_width)
        self.expiry_bars = int(expiry_bars)
        self.strategy_name = str(strategy_name)

        self._bars: Deque[Bar] = deque(maxlen=self.lookback + 2)  # keep a little extra
        self.box = DarvasBoxState()

        # Monotonic bar counter for expiry timing
        self._bar_index: int = -1

    # ---- Public API ----

    def on_bar(
        self,
        bar: Bar,
        position_state: PositionState,
    ) -> Signal:
        """
        Call once per new bar.

        You should pass your current position state (FLAT / LONG / SHORT / PENDING_*).
        SystemA will only emit ENTER_* if position_state == FLAT.

        Returns a Signal with reason strings suitable for your logs.
        """
        self._bar_index += 1
        self._bars.append(bar)

        # Enforce one-trade-at-a-time at the strategy boundary
        if position_state != PositionState.FLAT:
            # While in position or pending, do not form or change boxes
            return Signal(
                strategy=self.strategy_name,
                action=Action.HOLD,
                strength=0.0,
                reason=f"system_a_veto_not_flat:{position_state.value}",
                tag="veto",
            )

        # Need enough history to compute a candidate box from prior lookback bars
        if len(self._bars) <= self.lookback:
            need = (self.lookback + 1) - len(self._bars)
            return Signal(
                strategy=self.strategy_name,
                action=Action.HOLD,
                strength=0.0,
                reason=f"darvas_warming_up_need_{need}_bars",
                tag="hold",
            )

        # If we have an active frozen box, only do breakout/expiry checks
        if self.box.is_active:
            sig = self._check_frozen_box_breakout_or_expiry(current_close=bar.close)
            return sig

        # Otherwise, attempt to form a box (confirm min_width closes inside)
        sig = self._form_and_maybe_freeze_box(current_close=bar.close)
        return sig

    # ---- Internal helpers ----

    def _prior_window(self) -> List[Bar]:
        """
        Returns the prior lookback bars excluding current bar.
        Assumes len(_bars) > lookback.
        """
        # Exclude last (current) bar
        bars_list = list(self._bars)
        return bars_list[-(self.lookback + 1) : -1]

    def _candidate_bounds(self) -> tuple[float, float]:
        window = self._prior_window()
        top = max(b.high for b in window)
        bottom = min(b.low for b in window)
        return top, bottom

    def _form_and_maybe_freeze_box(self, current_close: float) -> Signal:
        cand_top, cand_bottom = self._candidate_bounds()

        # Track candidate for logging clarity
        self.box.candidate_top = cand_top
        self.box.candidate_bottom = cand_bottom

        # "Inside" confirmation uses CLOSE, per your locked decision
        inside = (cand_bottom <= current_close <= cand_top)

        if inside:
            self.box.confirm_count += 1
        else:
            self.box.confirm_count = 0

        # If confirmed, freeze box
        if self.box.confirm_count >= self.min_width:
            self.box.is_active = True
            self.box.top = cand_top
            self.box.bottom = cand_bottom
            self.box.formed_at_index = self._bar_index

            return Signal(
                strategy=self.strategy_name,
                action=Action.HOLD,
                strength=0.0,
                reason=(
                    f"darvas_box_frozen"
                    f"|top={self._fmt(self.box.top)}"
                    f"|bot={self._fmt(self.box.bottom)}"
                    f"|confirm={self.box.confirm_count}/{self.min_width}"
                ),
                tag="box_frozen",
            )

        # Still forming
        return Signal(
            strategy=self.strategy_name,
            action=Action.HOLD,
            strength=0.0,
            reason=(
                f"darvas_box_forming"
                f"|confirm={self.box.confirm_count}/{self.min_width}"
                f"|cand_top={self._fmt(cand_top)}"
                f"|cand_bot={self._fmt(cand_bottom)}"
            ),
            tag="hold",
        )

    def _check_frozen_box_breakout_or_expiry(self, current_close: float) -> Signal:
        assert self.box.top is not None and self.box.bottom is not None
        assert self.box.formed_at_index is not None

        age = self._bar_index - self.box.formed_at_index
        if age > self.expiry_bars:
            old_top = self.box.top
            old_bot = self.box.bottom
            self.box.reset()
            return Signal(
                strategy=self.strategy_name,
                action=Action.HOLD,
                strength=0.0,
                reason=(
                    f"darvas_box_expired"
                    f"|age={age}"
                    f"|top={self._fmt(old_top)}"
                    f"|bot={self._fmt(old_bot)}"
                ),
                tag="box_expired",
            )

        # Breakout confirmation uses CLOSE beyond bounds
        if current_close > self.box.top:
            return Signal(
                strategy=self.strategy_name,
                action=Action.ENTER_LONG,
                strength=1.0,
                reason=f"darvas_breakout_up_close_over_top={self._fmt(self.box.top)}",
                tag="breakout",
            )

        if current_close < self.box.bottom:
            return Signal(
                strategy=self.strategy_name,
                action=Action.ENTER_SHORT,
                strength=1.0,
                reason=f"darvas_breakout_down_close_under_bot={self._fmt(self.box.bottom)}",
                tag="breakout",
            )

        return Signal(
            strategy=self.strategy_name,
            action=Action.HOLD,
            strength=0.0,
            reason=(
                f"darvas_box_active_no_breakout"
                f"|age={age}"
                f"|top={self._fmt(self.box.top)}"
                f"|bot={self._fmt(self.box.bottom)}"
            ),
            tag="hold",
        )

    @staticmethod
    def _fmt(x: Optional[float]) -> str:
        if x is None:
            return "None"
        # Format like your log examples (one decimal) but safe for integers too
        return f"{float(x):.1f}"


# -----------------------------
# Example usage (optional)
# -----------------------------
if __name__ == "__main__":
    sysa = SystemA()

    # Fake bars (high, low, close) just for sanity run
    # In your live code you'll call sysa.on_bar(...) each new bar.
    bars = [
        Bar(high=5001, low=4999, close=5000),
    ] * 25

    pos = PositionState.FLAT
    for b in bars:
        sig = sysa.on_bar(b, pos)
        print(sig)
        