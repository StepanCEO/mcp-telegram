"""Configuration for the Telegram MCP server."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """api_id/api_hash come from https://my.telegram.org -> API development tools."""

    api_id: int
    api_hash: str
    session_path: str


def load_settings() -> Settings:
    api_id = os.getenv("TELEGRAM_API_ID", "").strip()
    api_hash = os.getenv("TELEGRAM_API_HASH", "").strip()
    if not api_id or not api_hash:
        raise RuntimeError(
            "TELEGRAM_API_ID / TELEGRAM_API_HASH are not set. "
            "Get them at https://my.telegram.org and put them in .env "
            "(see .env.example)."
        )
    session = os.getenv("TELEGRAM_SESSION", str(Path.home() / ".mcp-telegram.session"))
    return Settings(api_id=int(api_id), api_hash=api_hash, session_path=session)
