"""One-time interactive login: creates the saved Telethon session.

    python -m mcp_telegram.login

Telethon asks for your phone number and the code Telegram sends you.
After this, the MCP server uses the saved session non-interactively.
"""

import asyncio

from telethon import TelegramClient

from .config import load_settings


async def main() -> None:
    settings = load_settings()
    client = TelegramClient(settings.session_path, settings.api_id, settings.api_hash)
    await client.start()  # interactive: phone + code (+ 2FA password if set)
    me = await client.get_me()
    print(f"Signed in as {me.first_name} (@{me.username}). Session: {settings.session_path}")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
