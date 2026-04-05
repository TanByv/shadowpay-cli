"""Rich panel builders for detailed views and status displays."""

from __future__ import annotations

from typing import Any

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .formatters import (
    format_date,
    format_float_value,
    format_liquidity,
    format_price,
    format_state,
)

# ── Balance ─────────────────────────────────────────────────────────────────


def build_balance_panel(balance: Any) -> Panel:
    """User balance panel."""
    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold bright_white", justify="right")
    table.add_column()

    table.add_row("Balance:", format_price(balance.balance))
    if balance.frozen_balance is not None:
        table.add_row("Frozen:", format_price(balance.frozen_balance))

    return Panel(
        table,
        title="[bold bright_cyan]💰 Account Balance[/]",
        border_style="bright_cyan",
        padding=(1, 3),
    )


def build_merchant_balance_panel(balance: Any) -> Panel:
    """Merchant balance panel."""
    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold bright_white", justify="right")
    table.add_column()

    table.add_row("Currency:", Text(balance.currency, style="bright_magenta"))
    table.add_row("Balance:", format_price(balance.balance))
    table.add_row("Deposit:", format_price(balance.deposit_balance))
    if balance.frozen_balance is not None:
        table.add_row("Frozen:", format_price(balance.frozen_balance))

    return Panel(
        table,
        title="[bold bright_cyan]🏦 Merchant Balance[/]",
        border_style="bright_cyan",
        padding=(1, 3),
    )


# ── Item Detail ─────────────────────────────────────────────────────────────


def build_item_detail_panel(item: Any, *, is_seller_online: bool = False) -> Panel:
    """Detailed item view with sticker info."""
    info = Table.grid(padding=(0, 2))
    info.add_column(style="bold bright_white", justify="right", min_width=16)
    info.add_column()

    # Name
    name = ""
    if hasattr(item, "steam_item") and item.steam_item:
        si = item.steam_item
        name = si.steam_market_hash_name or ""
        info.add_row("Name:", Text(name, style="bold white"))
        info.add_row("Exterior:", Text(si.exterior or "—", style="dim"))
        info.add_row("Type:", Text(si.type or "—", style="magenta"))
        info.add_row("Subcategory:", Text(si.subcategory or "—", style="dim"))
        info.add_row("Rarity:", Text(si.rarity or "—", style="yellow"))
        info.add_row("Suggested:", format_price(si.suggested_price))
        if si.liquidity is not None:
            info.add_row("Liquidity:", format_liquidity(si.liquidity))
        info.add_row("StatTrak™:", Text("Yes" if si.is_stattrak else "No", style="bright_red" if si.is_stattrak else "dim"))

    info.add_row("", Text(""))  # Spacer
    info.add_row("Item ID:", Text(str(item.id), style="bright_blue"))
    info.add_row("Price:", format_price(item.price))
    info.add_row("Float:", format_float_value(getattr(item, "floatvalue", None)))

    if getattr(item, "paintseed", None) is not None:
        info.add_row("Paint Seed:", Text(str(item.paintseed), style="dim"))
    if getattr(item, "paintindex", None) is not None:
        info.add_row("Paint Index:", Text(str(item.paintindex), style="dim"))

    info.add_row("State:", format_state(getattr(item, "state", None)))
    info.add_row("Created:", format_date(getattr(item, "time_created", None)))

    seller_icon = "🟢" if is_seller_online else "🔴"
    seller_text = "Online" if is_seller_online else "Offline"
    info.add_row(
        "Seller:",
        Text(f"{seller_icon} {seller_text}", style="bright_green" if is_seller_online else "dim red"),
    )

    # Stickers
    stickers = getattr(item, "stickers", [])
    if stickers:
        info.add_row("", Text(""))
        info.add_row("Stickers:", Text(f"{len(stickers)} applied", style="bright_magenta"))
        for i, st in enumerate(stickers, 1):
            st_name = st.steam_market_hash_name if hasattr(st, "steam_market_hash_name") else str(st)
            info.add_row(f"  #{i}:", Text(str(st_name), style="dim"))

    # Seller stats
    stats = getattr(item, "seller_stats", None)
    if stats:
        info.add_row("", Text(""))
        info.add_row("── Seller Stats ──", Text("", style="dim"))
        if stats.finished_percent_seven_days is not None:
            info.add_row("  7d Success:", Text(f"{stats.finished_percent_seven_days}%", style="bright_green"))
        if stats.finished_percent_fifteen_days is not None:
            info.add_row("  15d Success:", Text(f"{stats.finished_percent_fifteen_days}%", style="bright_green"))
        if stats.finished_seconds_seven_days is not None:
            info.add_row("  7d Avg Time:", Text(f"{stats.finished_seconds_seven_days}s", style="dim"))

    title_text = f"🔍 {name}" if name else "🔍 Item Detail"
    return Panel(
        info,
        title=f"[bold bright_cyan]{title_text}[/]",
        border_style="bright_cyan",
        padding=(1, 3),
    )


# ── Offer Detail ────────────────────────────────────────────────────────────


def build_offer_detail_panel(offer: Any, *, is_seller_online: bool = False) -> Panel:
    """Detailed offer view."""
    info = Table.grid(padding=(0, 2))
    info.add_column(style="bold bright_white", justify="right", min_width=16)
    info.add_column()

    name = ""
    if hasattr(offer, "steam_item") and offer.steam_item:
        name = offer.steam_item.steam_market_hash_name or ""
        info.add_row("Name:", Text(name, style="bold white"))
    elif hasattr(offer, "steam_market_hash_name") and offer.steam_market_hash_name:
        name = offer.steam_market_hash_name
        info.add_row("Name:", Text(name, style="bold white"))

    info.add_row("Offer ID:", Text(str(offer.id), style="bright_blue"))
    info.add_row("Price:", format_price(offer.price))
    info.add_row("Float:", format_float_value(getattr(offer, "floatvalue", None)))
    info.add_row("State:", format_state(getattr(offer, "state", None)))
    info.add_row("Created:", format_date(getattr(offer, "time_created", None)))

    seller_icon = "🟢" if is_seller_online else "🔴"
    seller_text = "Online" if is_seller_online else "Offline"
    info.add_row(
        "Seller:",
        Text(f"{seller_icon} {seller_text}", style="bright_green" if is_seller_online else "dim red"),
    )

    title_text = f"📋 {name}" if name else "📋 Offer Detail"
    return Panel(
        info,
        title=f"[bold bright_cyan]{title_text}[/]",
        border_style="bright_cyan",
        padding=(1, 3),
    )


# ── WebSocket Event ─────────────────────────────────────────────────────────

_EVENT_STYLES: dict[str, tuple[str, str]] = {
    "offer_created": ("🆕", "bright_green"),
    "offer_changed": ("🔄", "bright_yellow"),
    "sendOffer": ("📤", "bright_blue"),
    "acceptOffer": ("✅", "bright_green"),
    "cancelOffer": ("❌", "red"),
    "declineOffer": ("🚫", "bright_red"),
}


def build_ws_event_panel(event: Any) -> Panel:
    """Compact panel for a WebSocket event."""
    icon, colour = _EVENT_STYLES.get(event.event_type, ("📨", "white"))

    info = Table.grid(padding=(0, 2))
    info.add_column(style="bold bright_white", justify="right")
    info.add_column()

    info.add_row("Type:", Text(event.event_type, style=f"bold {colour}"))
    info.add_row("Channel:", Text(event.channel, style="dim"))

    # Show offers if present
    offers = event.data.get("offers", [])
    if offers:
        for offer_data in offers[:3]:  # Show max 3
            offer_name = offer_data.get("steam_market_hash_name", "—")
            offer_price = offer_data.get("price")
            price_text = f"${offer_price:.2f}" if offer_price else "—"
            info.add_row(
                "Item:",
                Text(f"{offer_name}  {price_text}", style="white"),
            )
        if len(offers) > 3:
            info.add_row("", Text(f"  … and {len(offers) - 3} more", style="dim"))

    return Panel(
        info,
        title=f"[bold {colour}]{icon} WebSocket Event[/]",
        border_style=colour,
        padding=(0, 2),
    )
