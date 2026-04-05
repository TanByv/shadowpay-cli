"""User-specific models: balance, websocket auth, trade report."""

from __future__ import annotations

from pydantic import BaseModel


class UserBalance(BaseModel):
    """User account balance."""

    balance: float = 0.0
    frozen_balance: float | None = None


class WebSocketAuth(BaseModel):
    """WebSocket authentication tokens returned by ``/user/websocket``."""

    token: str
    offers_token: str
    url: str


class TradeReportRequest(BaseModel):
    """Payload for ``POST /user/trade``."""

    trade_id: int
    tradeoffer_id: int
