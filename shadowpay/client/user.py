"""User API client – wraps all ``/user/*`` endpoints."""

from __future__ import annotations

from typing import Any

from ..models.items import Item, ItemPrice, SteamItem
from ..models.offers import CancelResult, Offer, UpdateResult
from ..models.operations import Operation
from ..models.user import UserBalance, WebSocketAuth
from .http import ShadowpayHttpClient


class UserClient:
    """High-level async client for the Shadowpay User API."""

    def __init__(self, http: ShadowpayHttpClient) -> None:
        self._http = http

    # ── Inventory ───────────────────────────────────────────────────────────

    async def get_inventory(self, project: str | None = None) -> list[dict[str, Any]]:
        """GET /user/inventory – fetch Steam inventory."""
        params: dict[str, Any] = {}
        if project:
            params["project"] = project
        resp = await self._http.get("/user/inventory", params=params)
        return resp.get("data", [])

    # ── Balance ─────────────────────────────────────────────────────────────

    async def get_balance(self) -> UserBalance:
        """GET /user/balance – current user balance."""
        resp = await self._http.get("/user/balance")
        return UserBalance.model_validate(resp.get("data", {}))

    # ── Items ───────────────────────────────────────────────────────────────

    async def get_items(
        self,
        *,
        project: str | None = None,
        steam_market_hash_name: list[str] | None = None,
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
        """GET /user/items – list items on sale with filtering."""
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
        if phases:
            params["phases"] = phases
        if ids:
            params["ids"] = ids

        resp = await self._http.get("/user/items", params=params)
        items = [Item.model_validate(i) for i in resp.get("data", [])]
        metadata = resp.get("metadata", {})
        return items, metadata

    async def get_item(self, item_id: int) -> tuple[Item, bool]:
        """GET /user/items/{id} – single item + seller online flag."""
        resp = await self._http.get(f"/user/items/{item_id}")
        data = resp.get("data", {})
        item = Item.model_validate(data.get("item", {}))
        is_online = data.get("is_seller_online", False)
        return item, is_online

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
        """GET /user/items/steam – steam item catalog."""
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

        resp = await self._http.get("/user/items/steam", params=params)
        items = [SteamItem.model_validate(i) for i in resp.get("data", [])]
        metadata = resp.get("metadata", {})
        return items, metadata

    async def get_item_prices(self, project: str | None = None) -> list[ItemPrice]:
        """GET /user/items/prices – price/volume list."""
        params: dict[str, Any] = {}
        if project:
            params["project"] = project
        resp = await self._http.get("/user/items/prices", params=params)
        return [ItemPrice.model_validate(p) for p in resp.get("data", [])]

    # ── Offers ──────────────────────────────────────────────────────────────

    async def get_offers(
        self,
        *,
        sort_column: str | None = None,
        sort_dir: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> tuple[list[Offer], dict[str, Any]]:
        """GET /user/offers – list active offers."""
        params: dict[str, Any] = {
            "sort_column": sort_column,
            "sort_dir": sort_dir,
            "limit": limit,
            "offset": offset,
        }
        resp = await self._http.get("/user/offers", params=params)
        offers = [Offer.model_validate(o) for o in resp.get("data", [])]
        metadata = resp.get("metadata", {})
        return offers, metadata

    async def get_offer(self, offer_id: int) -> tuple[Offer, bool]:
        """GET /user/offers/{id} – single offer + seller online flag."""
        resp = await self._http.get(f"/user/offers/{offer_id}")
        data = resp.get("data", {})
        offer = Offer.model_validate(data)
        is_online = data.get("is_seller_online", False)
        return offer, is_online

    async def create_offers(self, offers: list[dict[str, Any]]) -> list[Offer]:
        """POST /user/offers – create sell offers."""
        resp = await self._http.post("/user/offers", json_body={"offers": offers})
        return [Offer.model_validate(o) for o in resp.get("data", [])]

    async def update_offers(self, offers: list[dict[str, Any]]) -> UpdateResult:
        """PATCH /user/offers – update offer prices."""
        resp = await self._http.patch("/user/offers", json_body={"offers": offers})
        return UpdateResult.model_validate(resp)

    async def cancel_offers(self, item_ids: list[int]) -> CancelResult:
        """DELETE /user/offers – cancel specific offers (up to 100)."""
        resp = await self._http.delete("/user/offers", params={"item_ids": item_ids})
        return CancelResult.model_validate(resp)

    async def cancel_all_offers(self) -> CancelResult:
        """DELETE /user/offers/all – cancel all offers."""
        resp = await self._http.delete("/user/offers/all")
        return CancelResult.model_validate(resp)

    # ── Operations ──────────────────────────────────────────────────────────

    async def get_operations(
        self,
        *,
        states: list[str] | None = None,
        custom_ids: list[str] | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        sort_column: str | None = None,
        sort_dir: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        group_by: str | None = None,
        ids: list[int] | None = None,
    ) -> tuple[list[Operation], dict[str, Any]]:
        """GET /user/operations – operations history."""
        params: dict[str, Any] = {
            "date_from": date_from,
            "date_to": date_to,
            "sort_column": sort_column,
            "sort_dir": sort_dir,
            "limit": limit,
            "offset": offset,
            "group_by": group_by,
        }
        if states:
            params["states"] = states
        if custom_ids:
            params["custom_ids"] = custom_ids
        if ids:
            params["ids"] = ids

        resp = await self._http.get("/user/operations", params=params)
        ops = [Operation.model_validate(o) for o in resp.get("data", [])]
        metadata = resp.get("metadata", {})
        return ops, metadata

    # ── Token ───────────────────────────────────────────────────────────────

    async def update_token(self, access_token: str) -> dict[str, Any]:
        """PATCH /user/token – update Steam access token."""
        return await self._http.patch("/user/token", json_body={"access_token": access_token})

    # ── WebSocket ───────────────────────────────────────────────────────────

    async def get_websocket_auth(self) -> WebSocketAuth:
        """GET /user/websocket – get WS authentication tokens."""
        resp = await self._http.get("/user/websocket")
        return WebSocketAuth.model_validate(resp.get("data", {}))

    # ── Buy ─────────────────────────────────────────────────────────────────

    async def buy_item(
        self,
        *,
        item_id: int,
        steamid: str,
        trade_token: str,
        price: float | None = None,
        custom_id: str | None = None,
    ) -> dict[str, Any]:
        """POST /user/items/buy – buy item by ID."""
        body: dict[str, Any] = {
            "id": item_id,
            "steamid": steamid,
            "trade_token": trade_token,
        }
        if price is not None:
            body["price"] = price
        if custom_id:
            body["custom_id"] = custom_id
        resp = await self._http.post("/user/items/buy", json_body=body)
        return resp.get("data", {})

    # ── Trade ───────────────────────────────────────────────────────────────

    async def report_trade(self, trade_id: int, tradeoffer_id: int) -> dict[str, Any]:
        """POST /user/trade – report trade offer ID."""
        return await self._http.post(
            "/user/trade",
            json_body={"trade_id": trade_id, "tradeoffer_id": tradeoffer_id},
        )
