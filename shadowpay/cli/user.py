"""User subcommands – balance, inventory, items, offers, operations, token."""

from __future__ import annotations

from typing import Optional

import typer
from rich.prompt import Confirm

from ..client.http import ShadowpayHttpClient
from ..client.user import UserClient
from ..ui.panels import build_balance_panel, build_item_detail_panel, build_offer_detail_panel
from ..ui.tables import (
    build_inventory_table,
    build_items_table,
    build_offers_table,
    build_operations_table,
    build_prices_table,
    build_steam_items_table,
)
from .app import async_command, console, load_settings

user_app = typer.Typer(
    name="user",
    help="[bold cyan]User account[/] — balance, inventory, items, offers, operations.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


async def _user_client():
    """Create and return an entered HTTP client + UserClient."""
    cfg = load_settings()
    http = ShadowpayHttpClient(cfg.shadowpay_api_token, cfg.shadowpay_base_url)
    await http.__aenter__()
    return http, UserClient(http)


# ── Balance ─────────────────────────────────────────────────────────────────


@user_app.command("balance")
@async_command
async def balance() -> None:
    """Show your current Shadowpay balance."""
    http, client = await _user_client()
    try:
        bal = await client.get_balance()
        console.print(build_balance_panel(bal))
    finally:
        await http.__aexit__(None, None, None)


# ── Inventory ───────────────────────────────────────────────────────────────


@user_app.command("inventory")
@async_command
async def inventory(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Game: csgo, dota2, rust"),
) -> None:
    """List your Steam inventory items."""
    http, client = await _user_client()
    try:
        with console.status("[bold cyan]Fetching inventory…"):
            items = await client.get_inventory(project)
        if not items:
            console.print("[yellow]No inventory items found.[/]")
            return
        console.print(build_inventory_table(items))
        console.print(f"[dim]Total: {len(items)} items[/]")
    finally:
        await http.__aexit__(None, None, None)


# ── Items ───────────────────────────────────────────────────────────────────


@user_app.command("items")
@async_command
async def items(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Game filter"),
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search by name"),
    price_from: Optional[float] = typer.Option(None, "--price-from", help="Min price"),
    price_to: Optional[float] = typer.Option(None, "--price-to", help="Max price"),
    sort: str = typer.Option("price_market", "--sort", help="Sort column"),
    order: str = typer.Option("asc", "--order", "-o", help="Sort direction: asc/desc"),
    limit: int = typer.Option(25, "--limit", "-l", help="Results per page"),
    offset: int = typer.Option(0, "--offset", help="Results offset"),
) -> None:
    """List your items currently on sale."""
    http, client = await _user_client()
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
        console.print(build_items_table(result, title="Your Items on Sale"))
        total = metadata.get("total", len(result))
        console.print(f"[dim]Showing {len(result)} of {total} items (offset {offset})[/]")
    finally:
        await http.__aexit__(None, None, None)


# ── Item detail ─────────────────────────────────────────────────────────────


@user_app.command("item")
@async_command
async def item_detail(
    item_id: int = typer.Argument(..., help="Item ID to look up"),
) -> None:
    """Show detailed info for a single item."""
    http, client = await _user_client()
    try:
        with console.status("[bold cyan]Fetching item…"):
            item, is_online = await client.get_item(item_id)
        console.print(build_item_detail_panel(item, is_seller_online=is_online))
    finally:
        await http.__aexit__(None, None, None)


# ── Steam items ─────────────────────────────────────────────────────────────


@user_app.command("steam-items")
@async_command
async def steam_items(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Game filter"),
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search by name"),
    limit: int = typer.Option(25, "--limit", "-l", help="Results per page"),
    offset: int = typer.Option(0, "--offset", help="Results offset"),
) -> None:
    """Browse the Steam item catalog."""
    http, client = await _user_client()
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


# ── Prices ──────────────────────────────────────────────────────────────────


@user_app.command("prices")
@async_command
async def prices(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Game filter"),
) -> None:
    """Show current item prices and volumes."""
    http, client = await _user_client()
    try:
        with console.status("[bold cyan]Fetching prices…"):
            result = await client.get_item_prices(project)
        if not result:
            console.print("[yellow]No price data found.[/]")
            return
        console.print(build_prices_table(result))
        console.print(f"[dim]Total: {len(result)} items[/]")
    finally:
        await http.__aexit__(None, None, None)


# ── Offers ──────────────────────────────────────────────────────────────────


@user_app.command("offers")
@async_command
async def offers(
    sort: str = typer.Option("price", "--sort", help="Sort: id, price, time_created"),
    order: str = typer.Option("desc", "--order", "-o", help="asc / desc"),
    limit: int = typer.Option(25, "--limit", "-l", help="Results per page"),
    offset: int = typer.Option(0, "--offset", help="Results offset"),
) -> None:
    """List your active sell offers."""
    http, client = await _user_client()
    try:
        with console.status("[bold cyan]Fetching offers…"):
            result, metadata = await client.get_offers(
                sort_column=sort,
                sort_dir=order,
                limit=limit,
                offset=offset,
            )
        if not result:
            console.print("[yellow]No active offers.[/]")
            return
        console.print(build_offers_table(result, title="Your Active Offers"))
        total = metadata.get("total", len(result))
        console.print(f"[dim]Showing {len(result)} of {total} offers[/]")
    finally:
        await http.__aexit__(None, None, None)


@user_app.command("offer")
@async_command
async def offer_detail(
    offer_id: int = typer.Argument(..., help="Offer ID to look up"),
) -> None:
    """Show detailed info for a single offer."""
    http, client = await _user_client()
    try:
        with console.status("[bold cyan]Fetching offer…"):
            offer, is_online = await client.get_offer(offer_id)
        console.print(build_offer_detail_panel(offer, is_seller_online=is_online))
    finally:
        await http.__aexit__(None, None, None)


# ── Create offers ───────────────────────────────────────────────────────────


@user_app.command("create-offer")
@async_command
async def create_offer(
    asset_id: str = typer.Argument(..., help="Steam asset ID from inventory"),
    price: float = typer.Argument(..., help="Listing price in USD"),
    project: str = typer.Option("csgo", "--project", "-p", help="Game project"),
    currency: Optional[str] = typer.Option(None, "--currency", help="Currency (default: USD)"),
) -> None:
    """Create a sell offer for an inventory item."""
    http, client = await _user_client()
    try:
        offer_data = {"id": asset_id, "price": price, "project": project}
        if currency:
            offer_data["currency"] = currency

        console.print(f"[bold]Creating offer:[/] {asset_id} @ ${price:.2f} ({project})")
        if not Confirm.ask("[yellow]Proceed?[/]"):
            console.print("[dim]Cancelled.[/]")
            return

        with console.status("[bold cyan]Creating offer…"):
            result = await client.create_offers([offer_data])
        console.print(f"[bold bright_green]✓ Created {len(result)} offer(s)[/]")
        if result:
            console.print(build_offers_table(result, title="Created Offers"))
    finally:
        await http.__aexit__(None, None, None)


# ── Update offers ───────────────────────────────────────────────────────────


@user_app.command("update-offer")
@async_command
async def update_offer(
    offer_id: str = typer.Argument(..., help="Offer ID to update"),
    price: float = typer.Argument(..., help="New price"),
    currency: Optional[str] = typer.Option(None, "--currency", help="Currency"),
) -> None:
    """Update the price on an active offer."""
    http, client = await _user_client()
    try:
        update_data = {"id": offer_id, "price": price}
        if currency:
            update_data["currency"] = currency

        with console.status("[bold cyan]Updating offer…"):
            result = await client.update_offers([update_data])

        if result.updated_items:
            console.print(f"[bold bright_green]✓ Updated {len(result.updated_items)} offer(s)[/]")
            console.print(build_offers_table(result.updated_items, title="Updated"))
        if result.not_updated_items:
            console.print(f"[bold red]✗ Failed to update {len(result.not_updated_items)} offer(s)[/]")
        if result.errors:
            for err in result.errors:
                console.print(f"  [red]• ID {err.id}: {err.message}[/]")
    finally:
        await http.__aexit__(None, None, None)


# ── Cancel offers ───────────────────────────────────────────────────────────


@user_app.command("cancel-offers")
@async_command
async def cancel_offers(
    ids: list[int] = typer.Argument(..., help="Offer IDs to cancel"),
) -> None:
    """Cancel one or more offers by ID."""
    http, client = await _user_client()
    try:
        console.print(f"[bold yellow]Cancelling {len(ids)} offer(s)…[/]")
        if not Confirm.ask("[yellow]Proceed?[/]"):
            console.print("[dim]Cancelled.[/]")
            return

        with console.status("[bold cyan]Cancelling…"):
            result = await client.cancel_offers(ids)

        if result.cancelled_items:
            console.print(f"[bold bright_green]✓ Cancelled {len(result.cancelled_items)} offer(s)[/]")
        if result.not_cancelled_items:
            console.print(f"[bold red]✗ {len(result.not_cancelled_items)} could not be cancelled[/]")
        if result.errors:
            for err in result.errors:
                console.print(f"  [red]• ID {err.id}: {err.message}[/]")
    finally:
        await http.__aexit__(None, None, None)


@user_app.command("cancel-all")
@async_command
async def cancel_all() -> None:
    """Cancel ALL active offers (requires confirmation)."""
    http, client = await _user_client()
    try:
        console.print("[bold red]⚠ This will cancel ALL your active offers![/]")
        if not Confirm.ask("[bold red]Are you sure?[/]", default=False):
            console.print("[dim]Cancelled.[/]")
            return

        with console.status("[bold red]Cancelling all offers…"):
            result = await client.cancel_all_offers()

        if result.cancelled_items:
            console.print(f"[bold bright_green]✓ Cancelled {len(result.cancelled_items)} offer(s)[/]")
        if result.not_cancelled_items:
            console.print(f"[bold red]✗ {len(result.not_cancelled_items)} could not be cancelled[/]")
    finally:
        await http.__aexit__(None, None, None)


# ── Operations ──────────────────────────────────────────────────────────────


@user_app.command("operations")
@async_command
async def operations(
    state: Optional[str] = typer.Option(None, "--state", help="Filter: active, cancelled, finished"),
    sort: str = typer.Option("time_created", "--sort", help="Sort column"),
    order: str = typer.Option("desc", "--order", "-o", help="asc / desc"),
    limit: int = typer.Option(25, "--limit", "-l", help="Results per page"),
    offset: int = typer.Option(0, "--offset", help="Results offset"),
) -> None:
    """View your trade operations history."""
    http, client = await _user_client()
    try:
        states = [state] if state else None
        with console.status("[bold cyan]Fetching operations…"):
            result, metadata = await client.get_operations(
                states=states,
                sort_column=sort,
                sort_dir=order,
                limit=limit,
                offset=offset,
            )
        if not result:
            console.print("[yellow]No operations found.[/]")
            return
        console.print(build_operations_table(result))
        total = metadata.get("total", len(result))
        console.print(f"[dim]Showing {len(result)} of {total} operations[/]")
    finally:
        await http.__aexit__(None, None, None)


# ── Token ───────────────────────────────────────────────────────────────────


@user_app.command("update-token")
@async_command
async def update_token(
    access_token: str = typer.Argument(..., help="New Steam web access token"),
) -> None:
    """Update your Steam web access token."""
    http, client = await _user_client()
    try:
        with console.status("[bold cyan]Updating token…"):
            result = await client.update_token(access_token)
        status = result.get("status", "unknown")
        if status == "success":
            console.print("[bold bright_green]✓ Steam access token updated successfully.[/]")
        else:
            err = result.get("error_message", "unknown error")
            console.print(f"[bold red]✗ Failed: {err}[/]")
    finally:
        await http.__aexit__(None, None, None)


# ── Trade report ────────────────────────────────────────────────────────────


@user_app.command("report-trade")
@async_command
async def report_trade(
    trade_id: int = typer.Argument(..., help="Steam trade ID"),
    tradeoffer_id: int = typer.Argument(..., help="Steam trade offer ID"),
) -> None:
    """Report a trade offer ID to Shadowpay."""
    http, client = await _user_client()
    try:
        with console.status("[bold cyan]Reporting trade…"):
            result = await client.report_trade(trade_id, tradeoffer_id)
        status = result.get("status", "unknown")
        if status == "success":
            console.print("[bold bright_green]✓ Trade reported successfully.[/]")
        else:
            err = result.get("error_message", "unknown error")
            console.print(f"[bold red]✗ Failed: {err}[/]")
    finally:
        await http.__aexit__(None, None, None)


# ── Buy ─────────────────────────────────────────────────────────────────────


@user_app.command("buy")
@async_command
async def buy_item(
    item_id: int = typer.Argument(..., help="Item ID to buy"),
    steamid: str = typer.Argument(..., help="Your Steam ID"),
    trade_token: str = typer.Argument(..., help="Your Steam trade token"),
    price: Optional[float] = typer.Option(None, "--price", help="Max buy price"),
    custom_id: Optional[str] = typer.Option(None, "--custom-id", help="Custom order ID"),
) -> None:
    """Buy an item by its ID."""
    http, client = await _user_client()
    try:
        console.print(f"[bold]Buying item [bright_blue]{item_id}[/] …[/]")
        if not Confirm.ask("[yellow]Proceed with purchase?[/]"):
            console.print("[dim]Cancelled.[/]")
            return

        with console.status("[bold cyan]Processing purchase…"):
            result = await client.buy_item(
                item_id=item_id,
                steamid=steamid,
                trade_token=trade_token,
                price=price,
                custom_id=custom_id,
            )
        console.print("[bold bright_green]✓ Purchase initiated![/]")
        console.print(f"  Operation ID: [bright_blue]{result.get('id', '—')}[/]")
        console.print(f"  State: {result.get('state', '—')}")
    finally:
        await http.__aexit__(None, None, None)
