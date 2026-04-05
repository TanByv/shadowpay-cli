"""Merchant-specific models: balance, currency, buy request/result."""

from __future__ import annotations

from pydantic import BaseModel


class MerchantBalance(BaseModel):
    """Merchant account balance."""

    currency: str = "USD"
    deposit_balance: float = 0.0
    balance: float = 0.0
    frozen_balance: float | None = None


class CustomCurrency(BaseModel):
    """Payload for setting a custom merchant currency."""

    name: str
    rate: float


class BuyRequest(BaseModel):
    """Payload for ``POST /merchant/items/buy``."""

    id: str
    steamid: str
    trade_token: str
    custom_id: str | None = None
    price: float | None = None


class BuyForRequest(BaseModel):
    """Payload for ``POST /merchant/items/buy-for``."""

    steam_market_hash_name: str
    price: float
    steamid: str
    trade_token: str
    project: str
    custom_id: str | None = None
    phase: str | None = None


class BuyResult(BaseModel):
    """Result of a buy operation."""

    id: int | None = None
    type: str | None = None
    state: str | None = None
    price: float | None = None
    steam_trade_token: str | None = None
    steam_trade_offer_state: str | None = None
    steam_tradeofferid: str | None = None
    causer: str | None = None
    steamid: str | None = None
    time_created: str | None = None
    custom_id: str | None = None
    items: list[dict] | None = None

    model_config = {"extra": "allow"}
