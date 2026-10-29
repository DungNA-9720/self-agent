# Architecture

## Stack

| Piece | Choice | Why |
|---|---|---|
| Language | Python 3.13 (>=3.10 allowed) | simple, good libs |
| Package mgr | uv (`pyproject.toml` + `uv.lock`) | fast, reproducible |
| Chat UI | `discord.py` >=2.4 | user already lives in Discord |
| LLM | `ollama` AsyncClient, default `qwen3.5:9b` | local, private, supports tool calling |
| Trello | `requests` against REST API v1 | 5 endpoints, no SDK needed |
| Config | `python-dotenv` reading `.env` | |

## Flow

```
Discord message
  └─ on_message: filter (not bot, == DISCORD_USER_ID, channel match, non-empty)
       ├─ "!reset" → clear history[channel]
       └─ async with lock + typing():
            ask_model(channel_id, text)
              messages = [system_prompt(), *history[channel], user]
              loop ≤ MAX_TOOL_ROUNDS (6):
                ollama.chat(model, messages, tools=TOOL_SPECS, temperature 0.3)
                no tool_calls → answer, stop
                else run_tool() each call (in thread) → append {"role":"tool"} → repeat
              history[channel] += user text + final answer only
       └─ reply in 1900-char chunks
```

## Components (`trello_agent/` package)

Imports flow one way: `config` ← `trello` ← `tools` ← `agent` ← `discord_bot` ← `__main__`.

- **`config.py`** – env vars read at import; required ones use `os.environ[...]` so missing values crash at startup.
- **`trello.py` → `trello(method, path, **params)`** – single HTTP helper, adds key/token, 15 s timeout, raises on HTTP error.
- **`_find(items, name, kind)`** – case-insensitive lookup: exact match first, then unique substring; raises `LookupError` (Vietnamese message telling the model to ask the user) on 0 or >1 matches.
- **Tools** (functions in `trello.py`; `TOOLS` dict + `TOOL_SPECS` JSON schemas in `tools.py`):

  | Tool | Args | Trello call |
  |---|---|---|
  | `list_columns` | – | `GET /boards/{id}/lists` |
  | `list_cards` | `column?` | `GET /boards/{id}/cards` (+ filter) |
  | `create_card` | `name, column, description?, due?` | `POST /cards` |
  | `move_card` | `card, column` | `PUT /cards/{id}` |
  | `add_comment` | `card, text` | `POST /cards/{id}/actions/comments` |

- **`tools.py` → `run_tool`** – runs tool via `asyncio.to_thread` (requests is blocking), always returns a JSON string; converts `LookupError`, bad args, HTTP errors, connection errors into `{"error": ...}` so the model can recover.
- **`agent.py` → `system_prompt()`, `ask_model()`** – Vietnamese prompt; injects today's date and weekday (`Thứ 2`..`Thứ 7`, `Chủ nhật`); tells model never to invent names and to ask on errors/ambiguity.
- **`discord_bot.py`** – client, `on_message` filtering, `!reset`, chunked replies, `run()`.
- **State** – `agent.history`: in-memory `defaultdict(deque(maxlen=20))` per channel. `discord_bot.lock`: one global `asyncio.Lock`, so messages are processed one at a time.

## Tuning knobs (`config.py`, temperature in `agent.py`)

- `HISTORY_LEN = 20` – messages remembered per channel
- `MAX_TOOL_ROUNDS = 6` – tool loop cap per message
- `temperature 0.3` in `ask_model`
- `OLLAMA_THINK=false` – passes `think=False` to Ollama

## Trade-offs

- **Package split by concern** – config / Trello / tool registry / LLM loop / Discord, each one file. No classes or interfaces; plain module functions.
- **Global lock** – fine for one user; per-channel locks if it ever serves more.
- **Only final Q/A stored in history** – keeps context small for a 9B model, but model forgets tool results (card IDs, lists) between turns and re-queries.
- **Name-based lookup** – friendly for chat, but re-fetches lists/cards on every tool call (no cache).
- **In-memory history** – lost on restart; acceptable for personal use.
