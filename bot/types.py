"""
TypedDict definitions for structured data flowing through the trading bot.

These types document the expected shapes of validated orders and Binance API
responses, making function signatures and call sites self-documenting without
adding runtime overhead.
"""
from typing import Optional, TypedDict

__all__ = ["OrderParams", "OrderResponse", "BalanceEntry"]


class OrderParams(TypedDict):
    """Validated order parameters returned by :func:`~bot.validators.validate_order_inputs`.

    All six keys are always present; ``price`` and ``stopPrice`` may be ``None``
    when not applicable to the order type.
    """

    symbol: str
    side: str
    type: str
    quantity: float
    price: Optional[float]
    stopPrice: Optional[float]


class OrderResponse(TypedDict, total=False):
    """Binance Futures order API response shape.

    ``total=False`` reflects that different endpoints return different subsets
    of these fields (e.g. ``/fapi/v1/algoOrder`` returns ``algoId`` instead of
    ``orderId``). The client normalises responses so ``orderId`` is always
    present after :meth:`~bot.client.BinanceFuturesClient.place_order` returns.
    """

    orderId: int
    algoId: int
    clientOrderId: str
    symbol: str
    side: str
    type: str
    origType: str
    status: str
    origQty: str
    executedQty: str
    cumQty: str
    cumQuote: str
    avgPrice: str
    price: str
    stopPrice: str
    timeInForce: str
    reduceOnly: bool
    positionSide: str
    closePosition: bool
    workingType: str
    priceProtect: bool
    priceMatch: str
    selfTradePreventionMode: str
    goodTillDate: int
    time: int
    updateTime: int


class BalanceEntry(TypedDict, total=False):
    """Single asset record from the ``/fapi/v2/balance`` endpoint."""

    accountAlias: str
    asset: str
    balance: str
    crossWalletBalance: str
    crossUnPnl: str
    availableBalance: str
    maxWithdrawAmount: str
    marginAvailable: bool
    updateTime: int
