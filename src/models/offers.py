"""Offer-related models: Offer, Create/Update/Cancel request & result."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .common import ErrorDetail
from .items import SteamItem


class Offer(BaseModel):
    """A sell offer on the Shadowpay marketplace."""

    id: int
    price: float
    floatvalue: float | None = None
    paintindex: int | None = None
    paintseed: int | None = None
    link: str | None = None
    state: str | None = None
    time_created: str | None = None
    project: str | None = None
    steam_market_hash_name: str | None = None
    steam_asset_id: str | None = None
    classid: str | None = None
    instanceid: str | None = None
    assetid: str | None = None
    stickers: list[SteamItem] = Field(default_factory=list)
    steam_item: SteamItem | None = None

    model_config = {"extra": "allow"}


# ── Request DTOs ────────────────────────────────────────────────────────────


class CreateOfferRequest(BaseModel):
    """Payload for creating a single offer."""

    id: str
    price: float
    project: str
    currency: str | None = None


class UpdateOfferRequest(BaseModel):
    """Payload for updating a single offer's price."""

    id: str
    price: float
    currency: str | None = None


# ── Batch Result DTOs ───────────────────────────────────────────────────────


class CancelResult(BaseModel):
    """Result of a batch cancel operation."""

    status: str = "success"
    cancelled_items: list[Offer] = Field(default_factory=list)
    not_cancelled_items: list[Offer] = Field(default_factory=list)
    errors: list[ErrorDetail] = Field(default_factory=list)


class UpdateResult(BaseModel):
    """Result of a batch update operation."""

    status: str = "success"
    updated_items: list[Offer] = Field(default_factory=list)
    not_updated_items: list[Offer] = Field(default_factory=list)
    errors: list[ErrorDetail] = Field(default_factory=list)
