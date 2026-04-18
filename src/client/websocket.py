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

    Usage::

        ws = ShadowpayWebSocket(token, offers_token, url)
        async for event in ws.listen():
            print(event)
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

    async def listen(self) -> AsyncIterator[WsEvent]:
        """Connect and yield events. Auto-reconnects on failure."""
        self._running = True
        delay = self._reconnect_delay

        while self._running:
            try:
                async with AsyncSession() as session:
                    ws = await session.ws_connect(self._url)
                    log.info("ws_connecting", url=self._url)

                    # Authenticate with personal channel token
                    auth_msg = orjson.dumps({"params": {"token": self._token}, "id": 1}).decode()
                    if self._debug_log:
                        log_raw_data("SEND", "WS", auth_msg)
                    await ws.send(auth_msg)

                    # Read auth response
                    auth_result: Any = await ws.recv()
                    auth_payload = auth_result[0] if isinstance(auth_result, tuple) else auth_result

                    if self._debug_log and auth_payload:
                        if isinstance(auth_payload, bytes):
                            auth_text = auth_payload.decode("utf-8", errors="replace")
                        else:
                            auth_text = str(auth_payload)
                        log_raw_data("RECV", "WS", auth_text)

                    if auth_payload:
                        # Ensure it's indexable (str/bytes)
                        msg_str = auth_payload[:200] if hasattr(auth_payload, "__getitem__") else str(auth_payload)
                        log.debug("ws_auth_response", data=msg_str)

                    # Subscribe to offers channel using offers_token
                    sub_msg = orjson.dumps(
                        {
                            "method": 1,
                            "params": {
                                "channel": "offers",
                                "token": self._offers_token,
                            },
                            "id": 2,
                        }
                    ).decode()
                    if self._debug_log:
                        log_raw_data("SEND", "WS", sub_msg)
                    await ws.send(sub_msg)

                    sub_result: Any = await ws.recv()
                    sub_payload = sub_result[0] if isinstance(sub_result, tuple) else sub_result
                    if self._debug_log and sub_payload:
                        if isinstance(sub_payload, bytes):
                            sub_text = sub_payload.decode("utf-8", errors="replace")
                        else:
                            sub_text = str(sub_payload)
                        log_raw_data("RECV", "WS", sub_text)
                    if sub_payload:
                        sub_msg_str = sub_payload[:200] if hasattr(sub_payload, "__getitem__") else str(sub_payload)
                        log.debug("ws_sub_response", data=sub_msg_str)

                    log.info("ws_connected", url=self._url)
                    delay = self._reconnect_delay  # Reset on success

                    # Main receive loop
                    while self._running:
                        try:
                            raw = await ws.recv()
                            if self._debug_log and raw:
                                pld = raw[0] if isinstance(raw, tuple) else raw
                                if isinstance(pld, bytes):
                                    txt = pld.decode("utf-8", errors="replace")
                                elif isinstance(pld, str):
                                    txt = pld
                                else:
                                    txt = str(pld)
                                log_raw_data("RECV", "WS", txt)
                        except Exception:
                            log.warning("ws_recv_error")
                            break

                        if raw is None:
                            log.warning("ws_closed")
                            break

                        # Centrifugo / curl_cffi returns (payload, opcode)
                        payload = raw[0] if isinstance(raw, tuple) else raw

                        if isinstance(payload, str):
                            text = payload
                        elif isinstance(payload, bytes):
                            text = payload.decode("utf-8", errors="replace")
                        else:
                            text = str(payload)

                        messages = self._parse_messages(text)

                        for msg in messages:
                            for event in self._extract_events(msg):
                                await self._notify(event)
                                yield event

            except Exception:
                log.exception("ws_connection_error")

            if self._running:
                log.info("ws_reconnecting", delay=delay)
                await asyncio.sleep(delay)
                delay = min(delay * 2, self._max_reconnect_delay)

    def stop(self) -> None:
        """Signal the listen loop to stop."""
        self._running = False
