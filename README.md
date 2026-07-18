# mcp-telegram

MCP (Model Context Protocol) server that connects Claude Desktop, Claude Code
or Cursor to your **personal Telegram account**. Ask your AI assistant in
plain language:

> «Что мне написали за утро? Суммаризируй рабочий чат.»
> «Найди сообщение, где Иван скидывал адрес офиса.»
> «Ответь Ивану, что буду в 15:00.»

The assistant picks the right tool, your account does the work.

## Tools

| Tool | What it does |
|------|--------------|
| `list_chats` | Recent chats, optionally only ones with unread messages |
| `read_chat` | Last N messages of a chat (by name, @username or id) |
| `search` | Full-text search in one chat or across all chats |
| `send_message` | Send a text message (only when you explicitly ask) |

Built on the official [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
(FastMCP) and [Telethon](https://github.com/LonamiWebs/Telethon) (MTProto —
your real account, not a bot; bots can't read your own chats).

## Setup

**1. Get Telegram API credentials** (2 minutes, one time):
go to [my.telegram.org](https://my.telegram.org) → API development tools →
create an app → copy `api_id` and `api_hash`.

**2. Install and log in:**

```bash
git clone https://github.com/StepanCEO/mcp-telegram
cd mcp-telegram
pip install -r requirements.txt
cp .env.example .env          # put api_id/api_hash there
python -m mcp_telegram.login  # one-time: phone number + code from Telegram
```

The login creates a session file (`~/.mcp-telegram.session`); after that the
server runs non-interactively.

**3. Wire it into your client.**

Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "telegram": {
      "command": "python",
      "args": ["-m", "mcp_telegram"],
      "cwd": "C:/path/to/mcp-telegram"
    }
  }
}
```

Claude Code:

```bash
claude mcp add telegram -- python -m mcp_telegram
```

Cursor (`.cursor/mcp.json`) — same shape as Claude Desktop.

Restart the client — the `telegram` tools appear automatically.

## Security notes

- The session file grants **full access to your account** — it stays on your
  machine, is never sent anywhere, and is `.gitignore`d. Treat it like a password.
- `send_message` is described to the model as "use only when the user
  explicitly asks", and MCP clients ask for your confirmation before tool
  calls by default.
- This is your personal account: respect Telegram's terms — no spam,
  no mass messaging.

## Tests

```bash
pip install pytest pytest-asyncio
pytest
```

Tests run against a fake Telethon client — no network or real account needed.
They cover unread filtering, message ordering, search, sending, and chat-id
parsing.

## Project structure

```
mcp_telegram/
├── server.py    # MCP tools (FastMCP, stdio transport)
├── service.py   # Telegram operations + formatting (testable core)
├── login.py     # one-time interactive sign-in
└── config.py    # .env settings
tests/
└── test_service.py
```

## License

MIT
