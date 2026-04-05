"""Shared enums, pagination metadata, and generic API response wrapper."""

from __future__ import annotations

from enum import IntEnum, StrEnum
from typing import Generic, TypeVar

from pydantic import BaseModel

# ── Enums ───────────────────────────────────────────────────────────────────


class Project(StrEnum):
    """Supported game projects."""

    CSGO = "csgo"
    DOTA2 = "dota2"
    RUST = "rust"


class SortDir(StrEnum):
    """Sort direction."""

    ASC = "asc"
    DESC = "desc"


class ResponseStatus(StrEnum):
    """Top-level status returned by the API."""

    SUCCESS = "success"
    ERROR = "error"


class TradeState(StrEnum):
    """Possible states of a trade operation."""

    ACTIVE = "active"
    FINISHED = "finished"
    CANCELLED = "cancelled"
    HOLD = "hold"


class TradeOfferState(IntEnum):
    """Steam trade offer state codes (0-11)."""

    NEW = 0
    PROCESSING_ERROR = 1
    ACTIVE = 2
    ACCEPTED = 3
    COUNTER_OFFER = 4
    EXPIRED = 5
    CANCELLED_BY_SENDER = 6
    CANCELLED_BY_RECIPIENT = 7
    ITEMS_UNAVAILABLE = 8
    WAITING_CONFIRMATION = 9
    CONFIRMATION_CANCELLED = 10
    ON_HOLD = 11

    @property
    def label(self) -> str:
        _labels = {
            0: "New",
            1: "Processing Error",
            2: "Active (waiting)",
            3: "Accepted",
            4: "Counter Offer",
            5: "Expired",
            6: "Cancelled (sender)",
            7: "Cancelled (recipient)",
            8: "Items Unavailable",
            9: "Waiting Confirmation",
            10: "Confirmation Cancelled",
            11: "On Hold (escrow)",
        }
        return _labels.get(self.value, f"Unknown ({self.value})")


class Causer(StrEnum):
    """Who caused a trade cancellation / rollback."""

    BUYER = "buyer"
    SELLER = "seller"


class Phase(StrEnum):
    """Doppler / gem phases."""

    PHASE_1 = "Phase 1"
    PHASE_2 = "Phase 2"
    PHASE_3 = "Phase 3"
    PHASE_4 = "Phase 4"
    SAPPHIRE = "Sapphire"
    RUBY = "Ruby"
    BLACK_PEARL = "Black Pearl"
    EMERALD = "Emerald"


# ── Pagination ──────────────────────────────────────────────────────────────


class PaginationMetadata(BaseModel):
    """Pagination metadata returned alongside list responses."""

    limit: int | None = None
    offset: int | None = None
    total: int | None = None


# ── Generic API Response ────────────────────────────────────────────────────

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Generic wrapper for every Shadowpay API response.

    The ``data`` field is generic - callers specify the concrete type.
    """

    status: ResponseStatus = ResponseStatus.SUCCESS
    data: T | None = None
    metadata: PaginationMetadata | None = None
    error_message: str | None = None
    code: int | None = None
    message: str | None = None

    @property
    def is_success(self) -> bool:
        return self.status == ResponseStatus.SUCCESS

    @property
    def is_error(self) -> bool:
        return self.status == ResponseStatus.ERROR


class ErrorDetail(BaseModel):
    """Per-item error in batch operations (cancel / update)."""

    id: int
    message: str = ""
