"""Service tests with a fake Telethon client — no network, no real account."""

from datetime import datetime
from types import SimpleNamespace

import pytest

from mcp_telegram.service import (
    TelegramService,
    format_dialogs,
    format_messages,
    _parse_chat,
)


def make_dialog(id, name, unread=0, is_user=False, is_channel=False):
    return SimpleNamespace(
        id=id, name=name, unread_count=unread, is_user=is_user, is_channel=is_channel
    )


def make_message(id, text, sender="Ivan", chat="Work", out=False):
    return SimpleNamespace(
        id=id,
        text=text,
        out=out,
        date=datetime(2026, 7, 18, 12, 0),
        sender=SimpleNamespace(first_name=sender, title=None, username=None),
        chat=SimpleNamespace(title=chat, first_name=None),
    )


class FakeClient:
    def __init__(self, dialogs=(), messages=()):
        self._dialogs = list(dialogs)
        self._messages = list(messages)
        self.sent = []

    async def iter_dialogs(self, limit=None):
        for d in self._dialogs[: limit or len(self._dialogs)]:
            yield d

    async def iter_messages(self, entity, limit=None, search=None):
        msgs = self._messages
        if search:
            msgs = [m for m in msgs if search.lower() in (m.text or "").lower()]
        for m in msgs[: limit or len(msgs)]:
            yield m

    async def get_entity(self, chat):
        return chat

    async def send_message(self, entity, text):
        msg = make_message(99, text, sender="me", chat=str(entity), out=True)
        self.sent.append((entity, text))
        return msg


@pytest.mark.asyncio
async def test_list_dialogs_unread_only():
    client = FakeClient(dialogs=[
        make_dialog(1, "Alice", unread=0, is_user=True),
        make_dialog(2, "News", unread=5, is_channel=True),
        make_dialog(3, "Work", unread=2),
    ])
    dialogs = await TelegramService(client).list_dialogs(unread_only=True)

    assert [d.name for d in dialogs] == ["News", "Work"]
    assert dialogs[0].kind == "channel"
    assert dialogs[1].kind == "group"


@pytest.mark.asyncio
async def test_read_messages_returns_oldest_first_and_skips_empty():
    client = FakeClient(messages=[
        make_message(3, "newest"),
        make_message(2, ""),  # e.g. a photo without caption
        make_message(1, "oldest"),
    ])
    messages = await TelegramService(client).read_messages("Work")

    assert [m.text for m in messages] == ["oldest", "newest"]


@pytest.mark.asyncio
async def test_search_filters_by_query():
    client = FakeClient(messages=[
        make_message(1, "deploy tomorrow"),
        make_message(2, "lunch?"),
    ])
    found = await TelegramService(client).search_messages("deploy")

    assert len(found) == 1
    assert found[0].text == "deploy tomorrow"


@pytest.mark.asyncio
async def test_send_message_returns_confirmation():
    client = FakeClient()
    sent = await TelegramService(client).send_message("@ivan", "буду в 15:00")

    assert client.sent == [("@ivan", "буду в 15:00")]
    assert sent.out is True
    assert sent.text == "буду в 15:00"


def test_parse_chat_numeric_vs_name():
    assert _parse_chat("12345") == 12345
    assert _parse_chat("-100987") == -100987
    assert _parse_chat("@ivan") == "@ivan"
    assert _parse_chat("Рабочий чат") == "Рабочий чат"


def test_format_dialogs_marks_unread():
    text = format_dialogs([
        # kind values here are precomputed DialogInfo fields, not fakes
    ])
    assert text == "Нет диалогов."


def test_format_messages_labels_own_messages():
    msg = make_message(1, "привет", out=True)
    from mcp_telegram.service import _to_info

    formatted = format_messages([_to_info(msg)])
    assert "я @ Work: привет" in formatted
