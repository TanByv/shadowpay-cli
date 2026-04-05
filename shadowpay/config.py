"""Application configuration loaded from environment / .env file."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Global application settings.

    Values are read from environment variables (case-insensitive) and
    from a ``.env`` file located in the project root.
    """

    shadowpay_api_token: str = Field(
        ...,
        description="Bearer token for Shadowpay API authentication",
    )
    shadowpay_base_url: str = Field(
        default="https://api.shadowpay.com/api/v2",
        description="Shadowpay V2 API base URL",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging verbosity (DEBUG, INFO, WARNING, ERROR)",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }
