"""Merchant API client – wraps all ``/merchant/*`` endpoints."""

from __future__ import annotations

from typing import Any

from ..models.items import Item, ItemPrice, SteamItem
from ..models.merchant import BuyResult, MerchantBalance
from ..models.operations import Operation
from .http import ShadowpayHttpClient


class MerchantClient:
    """High-level async client for the Shadowpay Merchant API."""

    def __init__(self, http: ShadowpayHttpClient) -> None:
        self._http = http

    # ── Balance ─────────────────────────────────────────────────────────────

    async def get_balance(self) -> MerchantBalance:
        """GET /merchant/balance – merchant account balance."""
        resp = await self._http.get("/merchant/balance")
        return MerchantBalance.model_validate(resp.get("data", {}))

    # ── Currency ────────────────────────────────────────────────────────────

    async def set_currency(self, name: str, rate: float) -> dict[str, Any]:
        """POST /merchant/currency – set custom currency."""
        return await self._http.post(
            "/merchant/currency",
            json_body={"name": name, "rate": rate},
        )

    async def disable_currency(self) -> dict[str, Any]:
        """DELETE /merchant/currency – disable custom currency."""
        return await self._http.delete("/merchant/currency")

    # ── Items ───────────────────────────────────────────────────────────────

    async def get_items(
        self,
        *,
        project: str | None = None,
        steam_market_hash_name: list[str] | None = None,
        types: list[str] | None = None,
        exteriors: list[str] | None = None,
        rarities: list[str] | None = None,
        search: str | None = None,
        price_from: float | None = None,
        price_to: float | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        sort_column: str | None = None,
        sort_dir: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        phases: list[str] | None = None,
        ids: list[int] | None = None,
    ) -> tuple[list[Item], dict[str, Any]]:
        """GET /merchant/items – list marketplace items."""
        params: dict[str, Any] = {
            "project": project,
            "search": search,
            "price_from": price_from,
            "price_to": price_to,
            "date_from": date_from,
            "date_to": date_to,
            "sort_column": sort_column,
            "sort_dir": sort_dir,
            "limit": limit,
            "offset": offset,
        }
        if steam_market_hash_name:
            params["steam_market_hash_name"] = steam_market_hash_name
        if types:
            params["types"] = types
        if exteriors:
            params["exteriors"] = exteriors
        if rarities:
            params["rarities"] = rarities
        if phases:
            params["phases"] = phases
        if ids:
            params["ids"] = ids

        resp = await self._http.get("/merchant/items", params=params)
        items = [Item.model_validate(i) for i in resp.get("data", [])]
        metadata = resp.get("metadata", {})
        return items, metadata

    async def get_item(self, item_id: int | str) -> tuple[Item | None, bool]:
        """GET /merchant/items/{id} – single item detail."""
        resp = await self._http.get(f"/merchant/items/{item_id}")
        data = resp.get("data", {})
        if not data:
            return None, False
        item_data = data.get("item", data)
        item = Item.model_validate(item_data)
        is_online = data.get("is_seller_online", False)
        return item, is_online

    async def get_item_prices(
        self,
        *,
        project: str | None = None,
        phases: list[str] | None = None,
    ) -> list[ItemPrice]:
        """GET /merchant/items/prices – item price/volume data."""
        params: dict[str, Any] = {"project": project}
        if phases:
            params["phases"] = phases
        resp = await self._http.get("/merchant/items/prices", params=params)
        return [ItemPrice.model_validate(p) for p in resp.get("data", [])]

    async def get_steam_items(
        self,
        *,
        project: str | None = None,
        steam_market_hash_name: list[str] | None = None,
        search: str | None = None,
        sort_column: str | None = None,
        sort_dir: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> tuple[list[SteamItem], dict[str, Any]]:
        """GET /merchant/items/steam – steam item catalog."""
        params: dict[str, Any] = {
            "project": project,
            "search": search,
            "sort_column": sort_column,
            "sort_dir": sort_dir,
            "limit": limit,
            "offset": offset,
        }
        if steam_market_hash_name:
            params["steam_market_hash_name"] = steam_market_hash_name

        resp = await self._http.get("/merchant/items/steam", params=params)
        items = [SteamItem.model_validate(i) for i in resp.get("data", [])]
        metadata = resp.get("metadata", {})
        return items, metadata

    # ── Buy ─────────────────────────────────────────────────────────────────

    async def buy_item(
        self,
        *,
        item_id: str,
        steamid: str,
        trade_token: str,
        custom_id: str | None = None,
        price: float | None = None,
    ) -> BuyResult:
        """POST /merchant/items/buy – buy item by ID."""
        body: dict[str, Any] = {
            "id": item_id,
            "steamid": steamid,
            "trade_token": trade_token,
        }
        if custom_id:
            body["custom_id"] = custom_id
        if price is not None:
            body["price"] = price
        resp = await self._http.post("/merchant/items/buy", json_body=body)
        return BuyResult.model_validate(resp.get("data", {}))

    async def buy_for(
        self,
        *,
        steam_market_hash_name: str,
        price: float,
        steamid: str,
        trade_token: str,
        project: str,
        custom_id: str | None = None,
        phase: str | None = None,
    ) -> BuyResult:
        """POST /merchant/items/buy-for – buy by name + price."""
        body: dict[str, Any] = {
            "steam_market_hash_name": steam_market_hash_name,
            "price": price,
            "steamid": steamid,
            "trade_token": trade_token,
            "project": project,
        }
        if custom_id:
            body["custom_id"] = custom_id
        if phase:
            body["phase"] = phase
        resp = await self._http.post("/merchant/items/buy-for", json_body=body)
        return BuyResult.model_validate(resp.get("data", {}))

    # ── Operations ──────────────────────────────────────────────────────────

    async def get_operations(
        self,
        *,
        type_filter: str | None = None,
        states: list[str] | None = None,
        custom_ids: list[str] | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        sort_column: str | None = None,
        sort_dir: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        operation_id: int | None = None,
        steamid: str | None = None,
        ids: list[int] | None = None,
    ) -> tuple[list[Operation], dict[str, Any]]:
        """GET /merchant/operations – operations history."""
        params: dict[str, Any] = {
            "type": type_filter,
            "date_from": date_from,
            "date_to": date_to,
            "sort_column": sort_column,
            "sort_dir": sort_dir,
            "limit": limit,
            "offset": offset,
            "id": operation_id,
            "steamid": steamid,
        }
        if states:
            params["states"] = states
        if custom_ids:
            params["custom_ids"] = custom_ids
        if ids:
            params["ids"] = ids

        resp = await self._http.get("/merchant/operations", params=params)
        ops = [Operation.model_validate(o) for o in resp.get("data", [])]
        metadata = resp.get("metadata", {})
        return ops, metadata
