# Shadowpay CLI

A production-quality interactive CLI for the [Shadowpay V2 API](https://docs.shadowpay.com), built with modern Python.

![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue)

## Features

- **Full API Coverage** — all User and Merchant V2 endpoints
- **Real-time WebSocket** — live offer/trade event streaming (fully supported via `curl_cffi`)
- **Rich Terminal UI** — colour-coded tables, panels, progress indicators
- **Async Architecture** — `curl_cffi` with TLS impersonation & automatic WebSocket payload parsing
- **Typed Models** — Pydantic v2 validation for every request/response
- **Auto Retry** — exponential backoff on transient errors (429 / 5xx)
- **Robustness** — automatic currency handling & PHP-compliant array parameter serialization

## Quick Start

### 1. Install dependencies

```bash
uv sync
```

### 2. Configure

Copy the example and add your API token:

```bash
cp .env.example .env
# Edit .env and set SHADOWPAY_API_TOKEN
```

### 3. Run

```bash
uv run python main.py --help
```

## Commands

### User

```
user balance          Show account balance
user inventory        List Steam inventory
user items            Search/list marketplace items (with filters)
user item <id>        Inspect a marketplace item
user steam-items      Browse Steam item catalog
user prices           Show price/volume data
user offers           List active sell offers
user offer <id>       Inspect a single offer
user create-offer     Create a sell offer
user update-offer     Update offer price
user cancel-offers    Cancel specific offers
user cancel-all       Cancel ALL offers
user operations       Trade operations history
user update-token     Update Steam access token
user report-trade     Report a trade offer ID
user buy              Buy an item by ID
```

### Merchant

```
merchant balance          Merchant account balance
merchant set-currency     Set custom currency rate
merchant disable-currency Disable custom currency
merchant items            Browse marketplace items
merchant item <id>        Inspect an item
merchant prices           Price/volume overview
merchant steam-items      Steam item catalog
merchant buy              Buy item by ID
merchant buy-for          Buy item by name + price
merchant operations       Operations history
```

### Market

```
market browse         Paginated market browser
market search <q>     Search items by name
market prices         Price overview (sorted by volume)
market inspect <id>   Detailed item view
```

### WebSocket

```
ws listen             Live event stream (Ctrl+C to stop)
ws auth               Show WebSocket auth tokens
```

## Usage Examples

```bash
# Check your balance
uv run python main.py user balance

# Browse CS2 items under $10
uv run python main.py market browse --project csgo --price-to 10

# Search for a specific skin
uv run python main.py market search "AK-47 | Redline"

# List your active offers sorted by price
uv run python main.py user offers --sort price --order asc

# Create a sell offer
uv run python main.py user create-offer 12345678 25.50 --project csgo

# Stream live marketplace events
uv run python main.py ws listen

# Stream events as raw JSON
uv run python main.py ws listen --raw

# Merchant: buy an item
uv run python main.py merchant buy 12345 76561198xxxxx trade_token_here
```

## Project Structure

```
shadowpay-cli/
├── main.py                  # Entry point
├── pyproject.toml
├── .env.example
└── src/
    ├── config.py            # Settings from .env
    ├── models/              # Pydantic v2 API models
    │   ├── common.py        # Enums, pagination, ApiResponse
    │   ├── items.py         # Item, SteamItem, ItemPrice
    │   ├── offers.py        # Offer, Create/Update/Cancel
    │   ├── operations.py    # Operation, OperationItem
    │   ├── user.py          # UserBalance, WebSocketAuth
    │   └── merchant.py      # MerchantBalance, BuyRequest
    ├── client/              # Async API clients
    │   ├── http.py          # Base HTTP client (curl_cffi + tenacity)
    │   ├── user.py          # UserClient — all /user/* endpoints
    │   ├── merchant.py      # MerchantClient — all /merchant/*
    │   └── websocket.py     # Centrifugo WebSocket client
    ├── cli/                 # Typer command groups
    │   ├── app.py           # Root app, banner, async helper
    │   ├── user.py          # User subcommands
    │   ├── merchant.py      # Merchant subcommands
    │   ├── market.py        # Market browsing commands
    │   └── ws.py            # WebSocket live stream
    └── ui/                  # Rich UI components
        ├── formatters.py    # Price, float, state, date formatters
        ├── tables.py        # Table builders for all data types
        └── panels.py        # Detail panels & balance displays
```

## Technology Stack

| Library | Purpose |
|---|---|
| `curl_cffi` | HTTP + WebSocket with TLS impersonation |
| `pydantic` v2 | API model validation |
| `rich` | Terminal UI (tables, panels, progress) |
| `typer` | CLI framework |
| `structlog` | Structured logging |
| `tenacity` | Retry with exponential backoff |
| `orjson` | Fast JSON serialization |
| `python-dotenv` | Environment configuration |

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `SHADOWPAY_API_TOKEN` | ✅ | — | Bearer token for API auth |
| `SHADOWPAY_BASE_URL` | ❌ | `https://api.shadowpay.com/api/v2` | API base URL |
| `LOG_LEVEL` | ❌ | `INFO` | Logging level |
