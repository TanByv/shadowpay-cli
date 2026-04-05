"""Root Typer application with shared state and helpers."""

from __future__ import annotations

import asyncio
from functools import wraps
from typing import Any, Callable, Coroutine, TypeVar

import structlog
import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ..client.http import ApiError
from ..config import Settings

# ── Structlog setup ─────────────────────────────────────────────────────────

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

log = structlog.get_logger()

# ── Console ─────────────────────────────────────────────────────────────────

console = Console()

# ── Async helper ────────────────────────────────────────────────────────────

F = TypeVar("F", bound=Callable[..., Coroutine[Any, Any, Any]])


# ── Error Message Mapping ───────────────────────────────────────────────────

ERROR_MESSAGES = {
    "bid_item_not_exist": "The requested offer (bid) does not exist or has been removed.",
    "wrong_params": "The request contains invalid parameters. Please check your command.",
    "permission_denied": "You do not have permission to perform this action.",
    "unauthorized": "Invalid API token. Please check your [bold].env[/] file.",
}


def async_command(func: F) -> Callable[..., Any]:
    """Decorator that turns an async function into a sync typer command."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return asyncio.run(func(*args, **kwargs))
        except ApiError as exc:
            # Format API Error
            console.print("\n")

            # Try to get a friendly message
            raw_msg = str(exc.error_message)
            friendly_msg = ERROR_MESSAGES.get(raw_msg, raw_msg or "An unexpected API error occurred.")

            console.print(
                Panel(
                    Text.from_markup(f"[bold red]API Error {exc.status_code}[/]\n\n" f"[white]{friendly_msg}[/]"),
                    title="[bold red]⚠ Error[/]",
                    border_style="red",
                    padding=(1, 3),
                    expand=False,
                )
            )
            if exc.body and raw_msg not in ERROR_MESSAGES:
                console.print(f"[dim]Code: {raw_msg}[/]")
            raise typer.Exit(1)
        except Exception as exc:
            # Format general exceptions
            console.print("\n")
            console.print(
                Panel(
                    Text.from_markup(
                        f"[bold red]Unexpected Exception[/]\n\n" f"[white]{type(exc).__name__}: {exc}[/]"
                    ),
                    title="[bold red]⚠ Error[/]",
                    border_style="red",
                    padding=(1, 3),
                    expand=False,
                )
            )
            # Log the full exception for debugging
            log.exception("unexpected_exception", exc=exc)
            raise typer.Exit(1)

    return wrapper


# ── Settings loader ─────────────────────────────────────────────────────────


def load_settings() -> Settings:
    """Load settings, printing a friendly error if the token is missing."""
    try:
        return Settings()  # type: ignore[call-arg]
    except Exception as exc:
        console.print(
            Panel(
                Text.from_markup(
                    "[bold red]Configuration Error[/]\n\n"
                    "Could not load settings. Make sure you have a [bold].env[/] file\n"
                    "with [bold cyan]SHADOWPAY_API_TOKEN[/] set.\n\n"
                    f"[dim]{exc}[/]"
                ),
                title="[bold red]⚠ Error[/]",
                border_style="red",
                padding=(1, 3),
            )
        )
        raise typer.Exit(1)


# ── Banner ──────────────────────────────────────────────────────────────────

BANNER = r"""
[bold bright_cyan]  _____ _               _                 ____
 / ____| |             | |               |  _ \  __ _ _   _
| (___ | |__   __ _  __| | _____      __ | |_) |/ _` | | | |
 \___ \| '_ \ / _` |/ _` |/ _ \ \ /\ / / |  __/ (_| | |_| |
 ____) | | | | (_| | (_| | (_) \ V  V /  | |  | (_,_|\__, |
|_____/|_| |_|\__,_|\__,_|\___/ \_/\_/   |_|   \__,_| __/ |
                                                      |___/ [/]
[dim]Interactive CLI for the Shadowpay V2 API[/]
"""


def print_banner() -> None:
    """Show the startup banner."""
    console.print(BANNER)


# ── App assembly ────────────────────────────────────────────────────────────


def create_app() -> typer.Typer:
    """Create and configure the root Typer application."""
    from .market import market_app
    from .merchant import merchant_app
    from .user import user_app
    from .ws import ws_app

    app = typer.Typer(
        name="shadowpay",
        help="Interactive CLI for the Shadowpay V2 API.",
        no_args_is_help=True,
        rich_markup_mode="rich",
        pretty_exceptions_enable=True,
        pretty_exceptions_show_locals=False,
    )

    app.add_typer(user_app, name="user", help="User account & inventory commands")
    app.add_typer(merchant_app, name="merchant", help="Merchant API commands")
    app.add_typer(market_app, name="market", help="Browse & search the marketplace")
    app.add_typer(ws_app, name="ws", help="WebSocket live event stream")

    @app.callback(invoke_without_command=True)
    def main_callback(ctx: typer.Context) -> None:
        """Shadowpay CLI – type a subcommand to get started."""
        if ctx.invoked_subcommand is None:
            print_banner()
            console.print("[dim]Run [bold]shadowpay --help[/bold] to see all commands.[/]\n")

    return app
