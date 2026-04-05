"""Rich table builders for Shadowpay data."""

from __future__ import annotations

from typing import Any

from rich.table import Table
from rich.text import Text

from .formatters import (
    format_date,
    format_float_value,
    format_liquidity,
    format_price,
    format_state,
    format_trade_offer_state,
)


def _truncate(text: str | None, max_len: int = 40) -> str:
    """Truncate long strings for table cells."""
    if not text:
        return "—"
    return text[:max_len] + "…" if len(text) > max_len else text


# ── Items ───────────────────────────────────────────────────────────────────

def build_items_table(items: list[Any], *, title: str = "Items") -> Table:
    """Build a rich table for Item objects."""
    table = Table(
        title=title,
        title_style="bold bright_cyan",
        border_style="bright_black",
        header_style="bold bright_white on grey23",
        row_styles=["", "on grey7"],
        expand=True,
        pad_edge=True,
        show_lines=False,
    )
    table.add_column("ID", justify="right", style="bright_blue", no_wrap=True)
    table.add_column("Name", style="white", ratio=3)
    table.add_column("Price", justify="right", no_wrap=True)
    table.add_column("Float", justify="right", no_wrap=True)
    table.add_column("Exterior", style="dim", no_wrap=True)
    table.add_column("State", justify="center", no_wrap=True)
    table.add_column("Stickers", justify="right", style="magenta", no_wrap=True)
    table.add_column("Created", justify="right", no_wrap=True)

    for item in items:
        name = ""
        exterior = ""
        if hasattr(item, "steam_item") and item.steam_item:
            name = item.steam_item.steam_market_hash_name or ""
            exterior = item.steam_item.exterior or ""
        elif hasattr(item, "steam_market_hash_name"):
            name = item.steam_market_hash_name or ""

        sticker_count = len(item.stickers) if hasattr(item, "stickers") else 0

        table.add_row(
            str(item.id),
            _truncate(name, 45),
            format_price(item.price),
            format_float_value(getattr(item, "floatvalue", None)),
            exterior or "—",
            format_state(getattr(item, "state", None)),
            str(sticker_count) if sticker_count else "—",
            format_date(getattr(item, "time_created", None)),
        )

    return table


# ── Offers ──────────────────────────────────────────────────────────────────

def build_offers_table(offers: list[Any], *, title: str = "Offers") -> Table:
    """Build a rich table for Offer objects."""
    table = Table(
        title=title,
        title_style="bold bright_cyan",
        border_style="bright_black",
        header_style="bold bright_white on grey23",
        row_styles=["", "on grey7"],
        expand=True,
    )
    table.add_column("ID", justify="right", style="bright_blue", no_wrap=True)
    table.add_column("Name", style="white", ratio=3)
    table.add_column("Price", justify="right", no_wrap=True)
    table.add_column("Float", justify="right", no_wrap=True)
    table.add_column("State", justify="center", no_wrap=True)
    table.add_column("Created", justify="right", no_wrap=True)

    for offer in offers:
        name = ""
        if hasattr(offer, "steam_item") and offer.steam_item:
            name = offer.steam_item.steam_market_hash_name or ""
        elif hasattr(offer, "steam_market_hash_name"):
            name = offer.steam_market_hash_name or ""

        table.add_row(
            str(offer.id),
            _truncate(name, 45),
            format_price(offer.price),
            format_float_value(getattr(offer, "floatvalue", None)),
            format_state(getattr(offer, "state", None)),
            format_date(getattr(offer, "time_created", None)),
        )

    return table


# ── Operations ──────────────────────────────────────────────────────────────

def build_operations_table(
    operations: list[Any], *, title: str = "Operations"
) -> Table:
    """Build a rich table for Operation objects."""
    table = Table(
        title=title,
        title_style="bold bright_cyan",
        border_style="bright_black",
        header_style="bold bright_white on grey23",
        row_styles=["", "on grey7"],
        expand=True,
    )
    table.add_column("ID", justify="right", style="bright_blue", no_wrap=True)
    table.add_column("Type", style="magenta", no_wrap=True)
    table.add_column("State", justify="center", no_wrap=True)
    table.add_column("Price", justify="right", no_wrap=True)
    table.add_column("Trade State", justify="center", no_wrap=True)
    table.add_column("SteamID", style="dim", no_wrap=True)
    table.add_column("Custom ID", style="dim")
    table.add_column("Created", justify="right", no_wrap=True)

    for op in operations:
        table.add_row(
            str(op.id),
            (op.type or "—").upper(),
            format_state(op.state),
            format_price(op.price),
            format_trade_offer_state(op.steam_trade_offer_state),
            _truncate(op.steamid, 18),
            _truncate(op.custom_id, 20),
            format_date(op.time_created),
        )

    return table


# ── Prices ──────────────────────────────────────────────────────────────────

def build_prices_table(
    prices: list[Any], *, title: str = "Market Prices"
) -> Table:
    """Build a rich table for ItemPrice objects."""
    table = Table(
        title=title,
        title_style="bold bright_cyan",
        border_style="bright_black",
        header_style="bold bright_white on grey23",
        row_styles=["", "on grey7"],
        expand=True,
    )
    table.add_column("#", justify="right", style="dim", no_wrap=True)
    table.add_column("Item Name", style="white", ratio=4)
    table.add_column("Min Price", justify="right", no_wrap=True)
    table.add_column("Volume", justify="right", style="bright_magenta", no_wrap=True)
    table.add_column("Liquidity", justify="right", no_wrap=True)
    table.add_column("Phase", style="cyan", no_wrap=True)

    for idx, p in enumerate(prices, 1):
        table.add_row(
            str(idx),
            _truncate(p.steam_market_hash_name, 55),
            format_price(p.price),
            str(p.volume),
            format_liquidity(getattr(p, "liquidity", None)),
            p.phase or "—",
        )

    return table


# ── Steam Items ─────────────────────────────────────────────────────────────

def build_steam_items_table(
    items: list[Any], *, title: str = "Steam Items"
) -> Table:
    """Build a rich table for SteamItem catalog objects."""
    table = Table(
        title=title,
        title_style="bold bright_cyan",
        border_style="bright_black",
        header_style="bold bright_white on grey23",
        row_styles=["", "on grey7"],
        expand=True,
    )
    table.add_column("ID", justify="right", style="bright_blue", no_wrap=True)
    table.add_column("Name", style="white", ratio=4)
    table.add_column("Suggested", justify="right", no_wrap=True)
    table.add_column("Exterior", style="dim", no_wrap=True)
    table.add_column("Type", style="magenta", no_wrap=True)
    table.add_column("Rarity", style="yellow", no_wrap=True)
    table.add_column("Liquidity", justify="right", no_wrap=True)

    for item in items:
        table.add_row(
            str(item.id),
            _truncate(item.steam_market_hash_name, 55),
            format_price(item.suggested_price),
            item.exterior or "—",
            item.type or "—",
            item.rarity or "—",
            format_liquidity(item.liquidity),
        )

    return table


# ── Inventory ───────────────────────────────────────────────────────────────

def build_inventory_table(
    items: list[dict[str, Any]], *, title: str = "Steam Inventory"
) -> Table:
    """Build a rich table for raw inventory dicts."""
    table = Table(
        title=title,
        title_style="bold bright_cyan",
        border_style="bright_black",
        header_style="bold bright_white on grey23",
        row_styles=["", "on grey7"],
        expand=True,
    )
    table.add_column("#", justify="right", style="dim", no_wrap=True)
    table.add_column("Asset ID", style="bright_blue", no_wrap=True)
    table.add_column("Name", style="white", ratio=4)
    table.add_column("Tradable", justify="center", no_wrap=True)

    for idx, item in enumerate(items, 1):
        asset_id = str(item.get("assetid", item.get("asset_id", "—")))
        name = item.get("market_hash_name", item.get("steam_market_hash_name", "—"))
        tradable = item.get("tradable", True)
        tradable_text = Text("✓", style="bright_green") if tradable else Text("✗", style="red")

        table.add_row(
            str(idx),
            asset_id,
            _truncate(str(name), 55),
            tradable_text,
        )

    return table
