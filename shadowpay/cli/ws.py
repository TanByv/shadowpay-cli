"""WebSocket live-stream subcommand – real-time marketplace events."""

from __future__ import annotations

import asyncio
from typing import Optional

import typer
from rich.panel import Panel
from rich.text import Text

from ..client.http import ShadowpayHttpClient
from ..client.user import UserClient
from ..client.websocket import ShadowpayWebSocket
from ..ui.panels import build_ws_event_panel
from .app import async_command, console, load_settings

ws_app = typer.Typer(
    name="ws",
    help="[bold cyan]WebSocket[/] — live real-time event stream.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


@ws_app.command("listen")
@async_command
async def listen(
    max_events: Optional[int] = typer.Option(None, "--max", "-n", help="Stop after N events (default: unlimited)"),
    raw: bool = typer.Option(False, "--raw", help="Print raw JSON instead of formatted panels"),
) -> None:
    """Connect to Shadowpay WebSocket and stream live events.

    Shows offer creations, changes, trade commands, and more in real-time.
    Press Ctrl+C to stop.
    """
    import orjson

    cfg = load_settings()
    http = ShadowpayHttpClient(cfg.shadowpay_api_token, cfg.shadowpay_base_url)

    try:
        await http.__aenter__()
        user_client = UserClient(http)

        # Get WebSocket auth tokens
        with console.status("[bold cyan]Authenticating for WebSocket…"):
            ws_auth = await user_client.get_websocket_auth()

        console.print(
            Panel(
                Text.from_markup(
                    f"[bold bright_green]✓ Connected to WebSocket[/]\n"
                    f"[dim]URL: {ws_auth.url}[/]\n"
                    f"[dim]Press [bold]Ctrl+C[/] to disconnect[/]"
                ),
                title="[bold bright_cyan]📡 Live Stream[/]",
                border_style="bright_cyan",
                padding=(1, 3),
            )
        )

        ws = ShadowpayWebSocket(
            token=ws_auth.token,
            offers_token=ws_auth.offers_token,
            url=ws_auth.url,
        )

        event_count = 0
        try:
            async for event in ws.listen():
                event_count += 1

                if raw:
                    console.print(orjson.dumps(event.raw, option=orjson.OPT_INDENT_2).decode())
                else:
                    console.print(build_ws_event_panel(event))

                if max_events and event_count >= max_events:
                    console.print(f"[dim]Reached {max_events} events, stopping.[/]")
                    ws.stop()
                    break
        except KeyboardInterrupt:
            ws.stop()
            console.print("\n[bold yellow]⏹ WebSocket disconnected.[/]")
        except asyncio.CancelledError:
            ws.stop()

    finally:
        await http.__aexit__(None, None, None)


@ws_app.command("auth")
@async_command
async def auth_info() -> None:
    """Show your WebSocket authentication tokens (for debugging)."""
    cfg = load_settings()
    http = ShadowpayHttpClient(cfg.shadowpay_api_token, cfg.shadowpay_base_url)

    try:
        await http.__aenter__()
        user_client = UserClient(http)

        with console.status("[bold cyan]Fetching WebSocket tokens…"):
            ws_auth = await user_client.get_websocket_auth()

        from rich.table import Table

        table = Table(
            title="WebSocket Auth Tokens",
            title_style="bold bright_cyan",
            border_style="bright_black",
            header_style="bold bright_white on grey23",
        )
        table.add_column("Property", style="bold bright_white")
        table.add_column("Value", style="dim")

        table.add_row("URL", ws_auth.url)
        table.add_row("Token", ws_auth.token[:40] + "…" if len(ws_auth.token) > 40 else ws_auth.token)
        table.add_row(
            "Offers Token",
            ws_auth.offers_token[:40] + "…" if len(ws_auth.offers_token) > 40 else ws_auth.offers_token,
        )

        console.print(table)
    finally:
        await http.__aexit__(None, None, None)
