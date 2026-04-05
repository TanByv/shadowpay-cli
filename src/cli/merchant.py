"""Merchant subcommands - balance, currency, items, buy, operations."""

from __future__ import annotations

from typing import Optional

import typer
from rich.prompt import Confirm

from ..client.http import ShadowpayHttpClient
from ..client.merchant import MerchantClient
from ..ui.panels import build_item_detail_panel, build_merchant_balance_panel
from ..ui.tables import (
    build_items_table,
    build_operations_table,
    build_prices_table,
    build_steam_items_table,
)
from .app import async_command, console, load_settings

merchant_app = typer.Typer(
    name="merchant",
    help="[bold cyan]Merchant API[/] — balance, items, buy, operations.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


async def _merchant_client():
    """Create and return an entered HTTP client + MerchantClient."""
    cfg = load_settings()
    http = ShadowpayHttpClient(cfg.shadowpay_api_token, cfg.shadowpay_base_url)
    await http.__aenter__()
    return http, MerchantClient(http)


# ── Balance ─────────────────────────────────────────────────────────────────


@merchant_app.command("balance")
@async_command
async def balance() -> None:
    """Show your merchant account balance."""
    http, client = await _merchant_client()
    try:
        bal = await client.get_balance()
        console.print(build_merchant_balance_panel(bal))
    finally:
        await http.__aexit__(None, None, None)


# ── Currency ────────────────────────────────────────────────────────────────


@merchant_app.command("set-currency")
@async_command
async def set_currency(
    name: str = typer.Argument(..., help="Currency name (e.g. 'Coin')"),
    rate: float = typer.Argument(..., help="Exchange rate to USD"),
) -> None:
    """Set a custom currency with a conversion rate."""
    http, client = await _merchant_client()
    try:
        with console.status("[bold cyan]Setting currency…"):
            result = await client.set_currency(name, rate)
        if result.get("status") == "success":
            console.print(f"[bold bright_green]✓ Currency set: {name} @ {rate}x[/]")
        else:
            console.print(f"[bold red]✗ Failed: {result}[/]")
    finally:
        await http.__aexit__(None, None, None)


@merchant_app.command("disable-currency")
@async_command
async def disable_currency() -> None:
    """Disable custom currency and revert to USD."""
    http, client = await _merchant_client()
    try:
        with console.status("[bold cyan]Disabling currency…"):
            result = await client.disable_currency()
        if result.get("status") == "success":
            console.print("[bold bright_green]✓ Custom currency disabled.[/]")
        else:
            console.print(f"[bold red]✗ Failed: {result}[/]")
    finally:
        await http.__aexit__(None, None, None)


# ── Items ───────────────────────────────────────────────────────────────────


@merchant_app.command("items")
@async_command
async def items(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Game filter"),
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search by name"),
    price_from: Optional[float] = typer.Option(None, "--price-from", help="Min price"),
    price_to: Optional[float] = typer.Option(None, "--price-to", help="Max price"),
    sort: str = typer.Option("price_market", "--sort", help="Sort column"),
    order: str = typer.Option("asc", "--order", "-o", help="asc / desc"),
    limit: int = typer.Option(25, "--limit", "-l", help="Results per page"),
    offset: int = typer.Option(0, "--offset", help="Results offset"),
) -> None:
    """Browse items available on the marketplace."""
    http, client = await _merchant_client()
    try:
        with console.status("[bold cyan]Fetching items…"):
            result, metadata = await client.get_items(
                project=project,
                search=search,
                price_from=price_from,
                price_to=price_to,
                sort_column=sort,
                sort_dir=order,
                limit=limit,
                offset=offset,
            )
        if not result:
            console.print("[yellow]No items found.[/]")
            return
        console.print(build_items_table(result, title="Marketplace Items"))
        total = metadata.get("total", len(result))
        console.print(f"[dim]Showing {len(result)} of {total} items (offset {offset})[/]")
    finally:
        await http.__aexit__(None, None, None)


@merchant_app.command("item")
@async_command
async def item_detail(
    item_id: int = typer.Argument(..., help="Item ID to look up"),
) -> None:
    """Show detailed info for a marketplace item."""
    http, client = await _merchant_client()
    try:
        with console.status("[bold cyan]Fetching item…"):
            item, is_online = await client.get_item(item_id)
        if item is None:
            console.print("[bold red]Item not found.[/]")
            return
        console.print(build_item_detail_panel(item, is_seller_online=is_online))
    finally:
        await http.__aexit__(None, None, None)


# ── Prices ──────────────────────────────────────────────────────────────────


@merchant_app.command("prices")
@async_command
async def prices(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Game filter"),
) -> None:
    """Show item prices and volumes on the marketplace."""
    http, client = await _merchant_client()
    try:
        with console.status("[bold cyan]Fetching prices…"):
            result = await client.get_item_prices(project=project)
        if not result:
            console.print("[yellow]No price data found.[/]")
            return
        console.print(build_prices_table(result, title="Merchant Prices"))
        console.print(f"[dim]Total: {len(result)} items[/]")
    finally:
        await http.__aexit__(None, None, None)


# ── Steam Items ─────────────────────────────────────────────────────────────


@merchant_app.command("steam-items")
@async_command
async def steam_items(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Game filter"),
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search by name"),
    limit: int = typer.Option(25, "--limit", "-l", help="Results per page"),
    offset: int = typer.Option(0, "--offset", help="Results offset"),
) -> None:
    """Browse the Steam item catalog."""
    http, client = await _merchant_client()
    try:
        with console.status("[bold cyan]Fetching steam items…"):
            result, metadata = await client.get_steam_items(
                project=project,
                search=search,
                limit=limit,
                offset=offset,
            )
        if not result:
            console.print("[yellow]No steam items found.[/]")
            return
        console.print(build_steam_items_table(result))
        total = metadata.get("total", len(result))
        console.print(f"[dim]Showing {len(result)} of {total} items[/]")
    finally:
        await http.__aexit__(None, None, None)


# ── Buy ─────────────────────────────────────────────────────────────────────


@merchant_app.command("buy")
@async_command
async def buy(
    item_id: str = typer.Argument(..., help="Item ID to buy"),
    steamid: str = typer.Argument(..., help="Buyer Steam ID"),
    trade_token: str = typer.Argument(..., help="Buyer trade token"),
    custom_id: Optional[str] = typer.Option(None, "--custom-id", help="Custom order ID"),
    price: Optional[float] = typer.Option(None, "--price", help="Max buy price"),
) -> None:
    """Buy an item by ID (merchant)."""
    http, client = await _merchant_client()
    try:
        console.print(f"[bold]Buying item [bright_blue]{item_id}[/]…[/]")
        if not Confirm.ask("[yellow]Proceed with purchase?[/]"):
            console.print("[dim]Cancelled.[/]")
            return

        with console.status("[bold cyan]Processing purchase…"):
            result = await client.buy_item(
                item_id=item_id,
                steamid=steamid,
                trade_token=trade_token,
                custom_id=custom_id,
                price=price,
            )
        console.print("[bold bright_green]✓ Purchase initiated![/]")
        console.print(f"  Operation ID: [bright_blue]{result.id}[/]")
        console.print(f"  State: {result.state or '—'}")
    finally:
        await http.__aexit__(None, None, None)


@merchant_app.command("buy-for")
@async_command
async def buy_for(
    name: str = typer.Argument(..., help="Steam market hash name"),
    price: float = typer.Argument(..., help="Max price to pay"),
    steamid: str = typer.Argument(..., help="Buyer Steam ID"),
    trade_token: str = typer.Argument(..., help="Buyer trade token"),
    project: str = typer.Option("csgo", "--project", "-p", help="Game project"),
    phase: Optional[str] = typer.Option(None, "--phase", help="Item phase"),
    custom_id: Optional[str] = typer.Option(None, "--custom-id", help="Custom order ID"),
) -> None:
    """Buy an item by name + max price (merchant)."""
    http, client = await _merchant_client()
    try:
        console.print(f'[bold]Buying "[bright_blue]{name}[/]" for ≤ ${price:.2f}…[/]')
        if not Confirm.ask("[yellow]Proceed?[/]"):
            console.print("[dim]Cancelled.[/]")
            return

        with console.status("[bold cyan]Processing purchase…"):
            result = await client.buy_for(
                steam_market_hash_name=name,
                price=price,
                steamid=steamid,
                trade_token=trade_token,
                project=project,
                custom_id=custom_id,
                phase=phase,
            )
        console.print("[bold bright_green]✓ Purchase initiated![/]")
        console.print(f"  Operation ID: [bright_blue]{result.id}[/]")
        console.print(f"  State: {result.state or '—'}")
    finally:
        await http.__aexit__(None, None, None)


# ── Operations ──────────────────────────────────────────────────────────────


@merchant_app.command("operations")
@async_command
async def operations(
    type_filter: Optional[str] = typer.Option(None, "--type", help="Filter: buy / sell"),
    state: Optional[str] = typer.Option(None, "--state", help="Filter: active, cancelled, finished"),
    steamid: Optional[str] = typer.Option(None, "--steamid", help="Filter by Steam ID"),
    sort: str = typer.Option("id", "--sort", help="Sort column"),
    order: str = typer.Option("desc", "--order", "-o", help="asc / desc"),
    limit: int = typer.Option(25, "--limit", "-l", help="Results per page"),
    offset: int = typer.Option(0, "--offset", help="Results offset"),
) -> None:
    """View merchant operations history."""
    http, client = await _merchant_client()
    try:
        states = [state] if state else None
        with console.status("[bold cyan]Fetching operations…"):
            result, metadata = await client.get_operations(
                type_filter=type_filter,
                states=states,
                steamid=steamid,
                sort_column=sort,
                sort_dir=order,
                limit=limit,
                offset=offset,
            )
        if not result:
            console.print("[yellow]No operations found.[/]")
            return
        console.print(build_operations_table(result, title="Merchant Operations"))
        total = metadata.get("total", len(result))
        console.print(f"[dim]Showing {len(result)} of {total} operations[/]")
    finally:
        await http.__aexit__(None, None, None)
