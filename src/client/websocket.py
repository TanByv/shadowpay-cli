"""WebSocket client for the Shadowpay Centrifugo-based real-time feed.

Implements the Centrifugo protocol over ``curl_cffi`` async websockets with
auto-reconnect and structured event parsing.
"""

from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator, Awaitable, Callable

import orjson
import structlog
from curl_cffi.requests import AsyncSession

from .debug import log_raw_data

log = structlog.get_logger()

# ── Event types ─────────────────────────────────────────────────────────────

WS_EVENT_OFFER_CREATED = "offer_created"
WS_EVENT_OFFER_CHANGED = "offer_changed"
WS_EVENT_SEND_OFFER = "sendOffer"
WS_EVENT_ACCEPT_OFFER = "acceptOffer"
WS_EVENT_CANCEL_OFFER = "cancelOffer"
WS_EVENT_DECLINE_OFFER = "declineOffer"


class WsEvent:
    """Parsed websocket event."""

    def __init__(
        self,
        event_type: str,
        channel: str,
        data: dict[str, Any],
        raw: dict[str, Any],
    ) -> None:
        self.event_type = event_type
        self.channel = channel
        self.data = data
        self.raw = raw

    def __repr__(self) -> str:
        return f"WsEvent(type={self.event_type!r}, channel={self.channel!r})"


EventCallback = Callable[[WsEvent], Awaitable[None]]


class ShadowpayWebSocket:
    """Async WebSocket client for Shadowpay real-time events.

    Handles multiple tokens by opening parallel connections if necessary
    (e.g., separate tokens for private events and market offers).
    """

    def __init__(
        self,
        token: str,
        offers_token: str,
        url: str,
        *,
        reconnect_delay: float = 2.0,
        max_reconnect_delay: float = 60.0,
        debug_log: bool = False,
    ) -> None:
        self._token = token
        self._offers_token = offers_token
        self._url = url
        self._reconnect_delay = reconnect_delay
        self._max_reconnect_delay = max_reconnect_delay
        self._debug_log = debug_log
        self._running = False
        self._callbacks: list[EventCallback] = []
        self._event_queue: asyncio.Queue[WsEvent] = asyncio.Queue()

    def on_event(self, callback: EventCallback) -> None:
        """Register a callback for incoming events."""
        self._callbacks.append(callback)

    async def _notify(self, event: WsEvent) -> None:
        for cb in self._callbacks:
            try:
                await cb(event)
            except Exception:
                log.exception("ws_callback_error", event=event)

    # ── Parsing ─────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_messages(raw_text: str) -> list[dict[str, Any]]:
        """Parse potentially concatenated JSON messages from Centrifugo.

        Centrifugo may send multiple JSON objects concatenated without a
        delimiter. We handle this by trying to decode each object boundary.
        """
        messages: list[dict[str, Any]] = []
        text = raw_text.strip()
        if not text:
            return messages

        # Try single parse first (most common case)
        try:
            obj = orjson.loads(text)
            if isinstance(obj, dict):
                messages.append(obj)
                return messages
            if isinstance(obj, list):
                return obj
        except Exception:
            pass

        # Concatenated JSON - split by finding object boundaries
        depth = 0
        start = 0
        for i, ch in enumerate(text):
            if ch == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        obj = orjson.loads(text[start : i + 1])
                        if isinstance(obj, dict):
                            messages.append(obj)
                    except Exception:
                        log.warning("ws_parse_error", fragment=text[start : i + 1][:80])
        return messages

    @staticmethod
    def _extract_events(message: dict[str, Any]) -> list[WsEvent]:
        """Extract WsEvent objects from a Centrifugo message."""
        events: list[WsEvent] = []

        # Handle publish messages
        result = message.get("result", {})
        if not result:
            return events

        channel = result.get("channel", "")
        pub_data = result.get("data", {})
        inner = pub_data.get("data", {})

        if not inner:
            return events

        event_type = inner.get("type", "unknown")
        events.append(
            WsEvent(
                event_type=event_type,
                channel=channel,
                data=inner,
                raw=message,
            )
        )
        return events

    # ── Connection ──────────────────────────────────────────────────────────

    async def _connection_loop(self, name: str, token: str) -> None:
        """Single connection loop for a specific token."""
        delay = self._reconnect_delay

        while self._running:
            try:
                async with AsyncSession() as session:
                    log.info("ws_connecting", name=name, url=self._url)
                    ws = await session.ws_connect(self._url)

                    # Handshake
                    auth_msg = orjson.dumps({"params": {"token": token}, "id": 1}).decode()
                    if self._debug_log:
                        log_raw_data("SEND", f"WS[{name}]", auth_msg)
                    await ws.send(auth_msg)

                    # Read auth response
                    raw = await ws.recv()
                    if raw is None:
                        raise ConnectionError("Connection closed during handshake")

                    payload = raw[0] if isinstance(raw, tuple) else raw
                    text = payload.decode("utf-8", errors="replace") if isinstance(payload, bytes) else str(payload)
                    if self._debug_log:
                        log_raw_data("RECV", f"WS[{name}]", text)

                    auth_data = orjson.loads(text)
                    if "error" in auth_data:
                        log.error("ws_auth_error", name=name, error=auth_data["error"])
                        raise PermissionError(auth_data["error"].get("message"))

                    log.info("ws_connected", name=name)
                    delay = self._reconnect_delay

                    # Main receive loop
                    while self._running:
                        raw = await ws.recv()
                        if raw is None:
                            log.warning("ws_closed", name=name)
                            break

                        payload = raw[0] if isinstance(raw, tuple) else raw
                        text = payload.decode("utf-8", errors="replace") if isinstance(payload, bytes) else str(payload)
                        if self._debug_log:
                            log_raw_data("RECV", f"WS[{name}]", text)

                        messages = self._parse_messages(text)
                        for msg in messages:
                            for event in self._extract_events(msg):
                                await self._event_queue.put(event)

            except asyncio.CancelledError:
                break
            except Exception as e:
                log.warning("ws_loop_error", name=name, error=str(e))

            if self._running:
                log.info("ws_reconnecting", name=name, delay=delay)
                await asyncio.sleep(delay)
                delay = min(delay * 2, self._max_reconnect_delay)

    async def listen(self, feeds: list[str] | None = None) -> AsyncIterator[WsEvent]:
        """Connect and yield events. Auto-reconnects on failure.

        Args:
            feeds: List of feeds to connect to ("account", "offers").
                  By default, all available feeds are connected.
        """
        self._running = True
        target_feeds = feeds if feeds is not None else ["account", "offers"]

        # Start connection loops
        tasks = []
        if "account" in target_feeds:
            tasks.append(asyncio.create_task(self._connection_loop("account", self._token)))
        if "offers" in target_feeds:
            tasks.append(asyncio.create_task(self._connection_loop("offers", self._offers_token)))

        if not tasks:
            log.warning("ws_no_feeds_selected")
            self._running = False
            return

        try:
            while self._running:
                event = await self._event_queue.get()
                await self._notify(event)
                yield event
        finally:
            self._running = False
            for t in tasks:
                t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

    def stop(self) -> None:
        """Signal the listen loop to stop."""
        self._running = False

