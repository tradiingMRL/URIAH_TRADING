from enum import Enum


class MarketRegime(Enum):
    TREND = "TREND"
    MEAN_REVERSION = "MEAN_REVERSION"
    CHAOTIC = "CHAOTIC"
    HALT = "HALT"


class TradePermission(Enum):
    ALLOW = "ALLOW"
    REDUCE = "REDUCE"
    BLOCK = "BLOCK"