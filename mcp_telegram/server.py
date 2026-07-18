"""MCP server: exposes Telegram tools over stdio.

Run directly for the first-time login (interactive code prompt):
    python -m mcp_telegram.login
Then wire it into Claude Desktop / Cursor (see README).
"""

import logging

from mcp.server.fastmcp import FastMCP
from telethon import TelegramClient

from .config import load_settings
from .service import TelegramService, format_dialogs, format_messages

logging.basicConfig(level=logging.WARNING)  # stdio transport: keep stdout clean

mcp = FastMCP("telegram")

_service: TelegramService | None = None


async def _get_service() -> TelegramService:
    """Lazily connect using the saved session (created by `login`)."""
    global _service
    if _service is None:
        settings = load_settings()
        client = TelegramClient(settings.session_path, settings.api_id, settings.api_hash)
        await client.connect()
        if not await client.is_user_authorized():
            raise RuntimeError(
                "Telegram session is not authorized. "
                "Run `python -m mcp_telegram.login` once to sign in."
            )
        _service = TelegramService(client)
    return _service


@mcp.tool()
async def list_chats(limit: int = 20, unread_only: bool = False) -> str:
    """List recent Telegram chats. Set unread_only=true to see only chats with unread messages."""
    service = await _get_service()
    return format_dialogs(await service.list_dialogs(limit=limit, unread_only=unread_only))


@mcp.tool()
async def read_chat(chat: str, limit: int = 30) -> str:
    """Read the last messages of a chat. `chat` is a chat name, @username or numeric id from list_chats."""
    service = await _get_service()
    return format_messages(await service.read_messages(chat, limit=limit))


@mcp.tool()
async def search(query: str, chat: str = "", limit: int = 20) -> str:
    """Search messages by text. Leave `chat` empty to search across all chats."""
    service = await _get_service()
    return format_messages(
        await service.search_messages(query, chat=chat or None, limit=limit)
    )


@mcp.tool()
async def send_message(chat: str, text: str) -> str:
    """Send a text message to a chat (name, @username or numeric id). Use only when the user explicitly asks to send something."""
    service = await _get_service()
    sent = await service.send_message(chat, text)
    return f"Отправлено в «{sent.chat}»: {sent.text}"


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
