"""Item-related models: SteamItem, Item, InventoryItem, ItemPrice, SellerStats."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SteamItemCollection(BaseModel):
    """Collection information attached to a steam item."""

    name: str | None = None
    color: str | None = None


class SteamItem(BaseModel):
    """Reference steam item (catalog entry)."""

    id: int
    project: str | None = None
    steam_market_hash_name: str = ""
    exterior: str | None = None
    type: str | None = None
    subcategory: str | None = None
    collection: SteamItemCollection | str | None = None
    phase: str | None = None
    suggested_price: float | None = None
    is_stattrak: bool = False
    icon: str | None = None
    rarity: str | None = None
    liquidity: float | None = None


class SellerStats(BaseModel):
    """Seller trade performance statistics."""

    finished_seconds_seven_days: int | None = None
    finished_seconds_fifteen_days: int | None = None
    finished_percent_seven_days: float | None = None
    finished_percent_fifteen_days: float | None = None
    finished_count_seven_days: int | None = None
    finished_count_fifteen_days: int | None = None


class Item(BaseModel):
    """An item listed on the Shadowpay marketplace.

    Used by both ``/user/items`` and ``/merchant/items`` endpoints.
    """

    id: int
    price: float
    floatvalue: float | None = None
    paintindex: int | None = None
    paintseed: int | None = None
    classid: str | None = None
    instanceid: str | None = None
    assetid: str | None = None
    link: str | None = None
    state: str | None = None
    time_created: str | None = None
    project: str | None = None
    steam_market_hash_name: str | None = None
    steam_asset_id: str | None = None
    stickers: list[SteamItem] = Field(default_factory=list)
    steam_item: SteamItem | None = None
    seller_stats: SellerStats | None = None


class InventoryItem(BaseModel):
    """A single item from the user's Steam inventory."""

    assetid: str | None = None
    classid: str | None = None
    instanceid: str | None = None
    market_hash_name: str | None = None
    icon_url: str | None = None
    tradable: bool | None = None
    # The API may return additional fields; Pydantic extra="allow" handles it.

    model_config = {"extra": "allow"}


class ItemPrice(BaseModel):
    """Price/volume summary for a steam item on Shadowpay."""

    steam_market_hash_name: str
    price: float
    volume: int
    liquidity: float | None = None
    phase: str | None = None
