"""Operation (trade) models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class OperationItem(BaseModel):
    """An item within a trade operation."""

    id: int | None = None
    state: str | None = None
    project: str | None = None
    steam_market_hash_name: str | None = None
    steam_asset_id: str | None = None
    price: float | None = None

    model_config = {"extra": "allow"}


class Operation(BaseModel):
    """A trade operation (buy / sell)."""

    id: int
    type: str | None = None
    state: str | None = None
    price: float | None = None
    steam_trade_token: str | None = None
    steam_trade_offer_state: int | str | None = None
    steam_tradeofferid: int | str | None = None
    steam_trade_offer_id: int | str | None = None
    steam_trade_offer_ids: str | list[str] | list[int] | None = None
    steam_to_steamid: str | None = None
    steam_from_steamid: str | None = None
    causer: str | None = None
    steamid: str | None = None
    time_created: str | None = None
    custom_id: str | None = None
    seller_sold: int | None = None
    items: list[OperationItem] = Field(default_factory=list)
    protected_items_status: int | str | None = None
    protected_items_until: str | None = None
    protected_items_causer: str | None = None

    model_config = {"extra": "allow"}
