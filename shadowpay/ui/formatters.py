"""Value formatting utilities – prices, floats, dates, states."""

from __future__ import annotations

from datetime import datetime

from rich.text import Text

# ── Price ───────────────────────────────────────────────────────────────────


def format_price(value: float | None, *, currency: str = "$") -> Text:
    """Format a monetary value with colour based on magnitude."""
    if value is None:
        return Text("—", style="dim")
    txt = f"{currency}{value:,.2f}"
    if value >= 100:
        return Text(txt, style="bold bright_green")
    if value >= 10:
        return Text(txt, style="green")
    if value >= 1:
        return Text(txt, style="yellow")
    return Text(txt, style="dim yellow")


# ── Float value (wear) ─────────────────────────────────────────────────────

_WEAR_BANDS: list[tuple[float, str, str]] = [
    (0.07, "Factory New", "bright_cyan"),
    (0.15, "Minimal Wear", "bright_green"),
    (0.38, "Field-Tested", "yellow"),
    (0.45, "Well-Worn", "dark_orange"),
    (1.00, "Battle-Scarred", "red"),
]


def format_float_value(value: float | None) -> Text:
    """Format a skin float value with wear-level colouring."""
    if value is None:
        return Text("—", style="dim")
    for threshold, _label, colour in _WEAR_BANDS:
        if value <= threshold:
            return Text(f"{value:.6f}", style=colour)
    return Text(f"{value:.6f}", style="red")


# ── State badges ────────────────────────────────────────────────────────────

_STATE_COLOURS: dict[str, str] = {
    "active": "bold bright_green",
    "finished": "bold cyan",
    "cancelled": "bold red",
    "hold": "bold yellow",
    "pending": "bold yellow",
    "success": "bold bright_green",
    "error": "bold red",
}


def format_state(state: str | None) -> Text:
    """Render a state string with a coloured badge."""
    if not state:
        return Text("—", style="dim")
    style = _STATE_COLOURS.get(state.lower(), "bold white")
    return Text(f" {state.upper()} ", style=f"{style} on grey23")


# ── Trade offer states ──────────────────────────────────────────────────────

_TRADE_STATE_MAP: dict[str, tuple[str, str]] = {
    "0": ("New", "bright_blue"),
    "1": ("Error", "red"),
    "2": ("Active", "bright_green"),
    "3": ("Accepted", "bold bright_cyan"),
    "4": ("Counter", "yellow"),
    "5": ("Expired", "dim red"),
    "6": ("Cancelled (sender)", "red"),
    "7": ("Cancelled (recipient)", "red"),
    "8": ("Items N/A", "dim red"),
    "9": ("Confirming", "yellow"),
    "10": ("Confirm cancelled", "red"),
    "11": ("On Hold", "bold yellow"),
}


def format_trade_offer_state(state: str | None) -> Text:
    """Human-readable trade offer state with colour."""
    if state is None:
        return Text("—", style="dim")
    label, colour = _TRADE_STATE_MAP.get(str(state), (f"Unknown ({state})", "dim"))
    return Text(label, style=colour)


# ── Date ────────────────────────────────────────────────────────────────────


def format_date(date_str: str | None) -> Text:
    """Format an API date string into a readable form."""
    if not date_str:
        return Text("—", style="dim")
    try:
        dt = datetime.fromisoformat(date_str.replace(" ", "T"))
        return Text(dt.strftime("%Y-%m-%d %H:%M"), style="bright_blue")
    except ValueError:
        return Text(date_str, style="dim")


# ── Liquidity ───────────────────────────────────────────────────────────────


def format_liquidity(value: float | None) -> Text:
    """Liquidity percentage with colour coding."""
    if value is None:
        return Text("—", style="dim")
    if value >= 75:
        return Text(f"{value:.1f}%", style="bold bright_green")
    if value >= 50:
        return Text(f"{value:.1f}%", style="green")
    if value >= 25:
        return Text(f"{value:.1f}%", style="yellow")
    return Text(f"{value:.1f}%", style="red")
