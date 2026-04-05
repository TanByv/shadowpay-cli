"""Market browsing subcommands - unified view across user/merchant item APIs."""

from __future__ import annotations

from typing import Optional

import typer

from ..client.http import ShadowpayHttpClient
from ..client.user import UserClient
from ..ui.panels import build_item_detail_panel
from ..ui.tables import build_items_table, build_prices_table
from .app import async_command, console, load_settings

market_app = typer.Typer(
    name="market",
    help="[bold cyan]Marketplace[/] — browse, search, and view prices.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


async def _user_client():
    cfg = load_settings()
    http = ShadowpayHttpClient(cfg.shadowpay_api_token, cfg.shadowpay_base_url)
    await http.__aenter__()
    return http, UserClient(http)


# ── Browse ──────────────────────────────────────────────────────────────────


@market_app.command("browse")
@async_command
async def browse(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Game filter"),
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search by name"),
    price_from: Optional[float] = typer.Option(None, "--price-from", help="Min price"),
    price_to: Optional[float] = typer.Option(None, "--price-to", help="Max price"),
    sort: str = typer.Option("price_market", "--sort", help="Sort: price_market, time_created, floatvalue"),
    order: str = typer.Option("asc", "--order", "-o", help="asc / desc"),
    limit: int = typer.Option(25, "--limit", "-l", help="Results per page"),
    offset: int = typer.Option(0, "--offset", help="Results offset"),
) -> None:
    """Browse items currently on sale on Shadowpay."""
    http, client = await _user_client()
    try:
        with console.status("[bold cyan]Loading marketplace…"):
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
            console.print("[yellow]No items found matching your criteria.[/]")
            return
        console.print(build_items_table(result, title="🛒 Shadowpay Market"))
        total = metadata.get("total", len(result))
        console.print(
            f"\n[dim]Showing {len(result)} of {total} items  •  "
            f"Page {(offset // limit) + 1}  •  "
            f"Use [bold]--offset {offset + limit}[/] for next page[/]"
        )
    finally:
        await http.__aexit__(None, None, None)


# ── Search ──────────────────────────────────────────────────────────────────


@market_app.command("search")
@async_command
async def search(
    query: str = typer.Argument(..., help="Search query (item name)"),
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Game filter"),
    limit: int = typer.Option(25, "--limit", "-l", help="Results limit"),
) -> None:
    """Search for items by name on the marketplace."""
    http, client = await _user_client()
    try:
        with console.status(f'[bold cyan]Searching for "{query}"…'):
            result, metadata = await client.get_items(
                project=project,
                search=query,
                limit=limit,
            )
        if not result:
            console.print(f'[yellow]No results for "{query}".[/]')
            return
        console.print(build_items_table(result, title=f'🔍 Results for "{query}"'))
        total = metadata.get("total", len(result))
        console.print(f"[dim]{total} total matches[/]")
    finally:
        await http.__aexit__(None, None, None)


# ── Prices ──────────────────────────────────────────────────────────────────


@market_app.command("prices")
@async_command
async def prices(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Game filter"),
) -> None:
    """Show current market prices with volume and liquidity data."""
    http, client = await _user_client()
    try:
        with console.status("[bold cyan]Fetching market prices…"):
            result = await client.get_item_prices(project)
        if not result:
            console.print("[yellow]No price data available.[/]")
            return
        # Sort by volume descending for most useful view
        result.sort(key=lambda p: p.volume, reverse=True)
        console.print(build_prices_table(result, title="📊 Market Prices"))
        console.print(f"[dim]{len(result)} items listed[/]")
    finally:
        await http.__aexit__(None, None, None)


# ── Item detail ─────────────────────────────────────────────────────────────


@market_app.command("inspect")
@async_command
async def inspect(
    item_id: int = typer.Argument(..., help="Item ID to inspect"),
) -> None:
    """Inspect a single marketplace item in detail."""
    http, client = await _user_client()
    try:
        with console.status("[bold cyan]Loading item…"):
            item, is_online = await client.get_item(item_id)
        console.print(build_item_detail_panel(item, is_seller_online=is_online))
    finally:
        await http.__aexit__(None, None, None)
