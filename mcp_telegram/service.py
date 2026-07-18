"""Telegram operations used by the MCP tools.

All methods take a Telethon-like client object; tests inject a fake with the
same surface. Formatting helpers are pure functions so the LLM-facing output
is testable without any network.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DialogInfo:
    id: int
    name: str
    kind: str  # user / group / channel
    unread: int


@dataclass(frozen=True)
class MessageInfo:
    id: int
    chat: str
    sender: str
    date: str  # ISO
    text: str
    out: bool  # sent by me


class TelegramService:
    """Thin async facade over a Telethon client."""

    def __init__(self, client):
        self._client = client

    async def list_dialogs(self, limit: int = 20, unread_only: bool = False) -> list[DialogInfo]:
        """Most recent chats, optionally only ones with unread messages."""
        dialogs = []
        async for d in self._client.iter_dialogs(limit=limit if not unread_only else limit * 3):
            if unread_only and d.unread_count == 0:
                continue
            dialogs.append(
                DialogInfo(
                    id=d.id,
                    name=d.name or "(без названия)",
                    kind=_dialog_kind(d),
                    unread=d.unread_count,
                )
            )
            if len(dialogs) >= limit:
                break
        return dialogs

    async def read_messages(self, chat: str, limit: int = 30) -> list[MessageInfo]:
        """Last messages from a chat (name, @username, or id), oldest first."""
        entity = await self._client.get_entity(_parse_chat(chat))
        messages = []
        async for m in self._client.iter_messages(entity, limit=limit):
            if not m.text:
                continue
            messages.append(_to_info(m))
        return list(reversed(messages))

    async def search_messages(self, query: str, chat: str | None = None, limit: int = 20) -> list[MessageInfo]:
        """Full-text search, in one chat or across all chats."""
        entity = await self._client.get_entity(_parse_chat(chat)) if chat else None
        messages = []
        async for m in self._client.iter_messages(entity, search=query, limit=limit):
            if m.text:
                messages.append(_to_info(m))
        return messages

    async def send_message(self, chat: str, text: str) -> MessageInfo:
        """Send a message; returns what was sent for confirmation."""
        entity = await self._client.get_entity(_parse_chat(chat))
        sent = await self._client.send_message(entity, text)
        return _to_info(sent)


def _dialog_kind(dialog) -> str:
    if getattr(dialog, "is_user", False):
        return "user"
    if getattr(dialog, "is_channel", False):
        return "channel"
    return "group"


def _parse_chat(chat: str):
    """Numeric ids stay ints; anything else (name/@username) passes through."""
    stripped = chat.strip()
    try:
        return int(stripped)
    except ValueError:
        return stripped


def _to_info(message) -> MessageInfo:
    sender = getattr(message, "sender", None)
    sender_name = (
        getattr(sender, "first_name", None)
        or getattr(sender, "title", None)
        or getattr(sender, "username", None)
        or "unknown"
    )
    chat_obj = getattr(message, "chat", None)
    chat_name = (
        getattr(chat_obj, "title", None)
        or getattr(chat_obj, "first_name", None)
        or "unknown"
    )
    date = getattr(message, "date", None)
    return MessageInfo(
        id=message.id,
        chat=chat_name,
        sender=sender_name,
        date=date.isoformat() if isinstance(date, datetime) else str(date),
        text=message.text or "",
        out=bool(getattr(message, "out", False)),
    )


def format_dialogs(dialogs: list[DialogInfo]) -> str:
    if not dialogs:
        return "Нет диалогов."
    lines = []
    for d in dialogs:
        unread = f" — {d.unread} непрочитанных" if d.unread else ""
        lines.append(f"[{d.id}] {d.name} ({d.kind}){unread}")
    return "\n".join(lines)


def format_messages(messages: list[MessageInfo]) -> str:
    if not messages:
        return "Сообщений не найдено."
    lines = []
    for m in messages:
        who = "я" if m.out else m.sender
        lines.append(f"[{m.date}] {who} @ {m.chat}: {m.text}")
    return "\n".join(lines)
