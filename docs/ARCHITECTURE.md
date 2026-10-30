# Architecture

## Stack

| Piece | Choice | Why |
|---|---|---|
| Language | Python 3.13 (>=3.10 allowed) | simple, good libs |
| Package mgr | uv (`pyproject.toml` + `uv.lock`) | fast, reproducible |
| Chat UI | `discord.py` >=2.4 | user already lives in Discord |
| LLM | `ollama` AsyncClient, default `qwen3.5:9b` | local, private, supports tool calling |
| Trello | `requests` against REST API v1 | 5 endpoints, no SDK needed |
| News | `requests` + stdlib `xml.etree` on VnExpress RSS 2.0 | no feed library needed |
| Config | `python-dotenv` reading `.env` | |

## Shape: one agent, tool groups

```
self_agent/
  agent.py  ──uses──▶  tools/__init__.py (registry: TOOLS, TOOL_SPECS, run_tool)
                          ├── trello/   TOOLS + SPECS
                          └── news/     TOOLS + SPECS
```

The agent sees one flat list of tool specs; groups only organize code. Imports flow one way:
`config` ← `tools/<group>` ← `tools/__init__` ← `agent` ← `morning` ← `discord_bot` ← `__main__`.

## Flow

```
Discord message
  └─ on_message: filter (not bot, == DISCORD_USER_ID, channel in CHANNEL_IDS or DM, non-empty)
       ├─ "!reset" → clear history[channel]
       ├─ "!morning" → send_morning(this channel)
       └─ async with lock + typing():
            ask_model(channel_id, text, channel_name)
              category_for_channel(name) → default_category ContextVar + hint in prompt
              messages = [system_prompt(category), *history[channel], user]
              loop ≤ MAX_TOOL_ROUNDS (6):
                ollama.chat(model, messages, tools=TOOL_SPECS, temperature 0.3)
                no tool_calls → answer, stop
                else run_tool() each call (in thread) → append {"role":"tool"} → repeat
              history[channel] += user text + final answer only
       └─ reply in 1900-char chunks

Daily at MORNING_TIME (discord.ext.tasks, tz-aware, default 08:00 Asia/Ho_Chi_Minh)
  └─ morning_job → morning_channel() (MORNING_CHANNEL_ID, else first DISCORD_CHANNEL_ID, else DM to user)
       └─ send_morning: async with lock
            morning_brief(channel_id)
              gather(run_tool get_news "Tin nổi bật" ×5, run_tool list_cards)   ← code, not model
              chat([system_prompt, PROMPT + JSON data], no tools) → greeting / news / tasks
              history[channel] += answer (so the user can ask follow-ups)
            model error → still sends a short greeting with the error
```

## Components

- **`config.py`** – env vars read at import; required ones use `os.environ[...]` so missing values crash at startup. Tuning constants.
- **`agent.py`** – `chat()` single Ollama call; `system_prompt(news_category)` (Vietnamese; today's date + weekday; never invent names; on news, summarize as bullets with links, only from tool output; channel's news category if any); `ask_model()` tool loop; `history`.
- **`morning.py`** – `morning_brief()`: data fetched deterministically in code (a 9B model may skip tool calls), model only formats: greeting with date, 3–5 impactful news with links, Trello: overdue / due today first, then cards grouped by column, done cards skipped.
- **`discord_bot.py`** – client, `on_message` filtering (DMs always allowed), `!reset`, `!morning`, chunked replies, global `lock`, `morning_job`, `run()`.
- **`tools/__init__.py`** – `GROUPS = [trello, news]`, merges `TOOLS` and `TOOL_SPECS`. `run_tool` runs a tool via `asyncio.to_thread` and always returns a JSON string, mapping errors to `{"error": ...}`:
  `LookupError` → message as is; `TypeError`/`ValueError` → bad args; `ET.ParseError` → bad RSS; `HTTPError` → status + body; other `RequestException` → exception class name only (URL could leak Trello token).
- **`tools/common.py`** – `spec()` / `s()` schema helpers; `find_by_name(items, name, kind)`: case-insensitive, exact match first, then unique substring; raises `LookupError` on 0 or >1 matches.

### Tool groups

**Trello** (`tools/trello/api.py`) – `trello()` HTTP helper adds key/token, 15 s timeout.

| Tool | Args | Trello call |
|---|---|---|
| `list_columns` | – | `GET /boards/{id}/lists` |
| `list_cards` | `column?` | `GET /boards/{id}/cards` (+ filter) |
| `create_card` | `name, column, description?, due?` | `POST /cards` |
| `move_card` | `card, column` | `PUT /cards/{id}` |
| `add_comment` | `card, text` | `POST /cards/{id}/actions/comments` |

**News** (`tools/news/vnexpress.py`)

| Tool | Args | Source |
|---|---|---|
| `get_news` | `category?` (default: channel's category, else "Tin mới nhất"), `limit?` (default 10, clamped 1–30) | `GET https://vnexpress.net/rss/{slug}.rss` |

- `CATEGORIES` maps Vietnamese names (Tin mới nhất, Tin nổi bật, Thời sự, Thế giới, Kinh doanh, Thể thao, …, 19 total) to feed slugs. Category accepts a name (fuzzy via `find_by_name`) or a slug.
- Only items published within `MAX_AGE_DAYS = 3` are returned; items without a parsable `pubDate` are dropped.
- `parse_rss` returns `title`, `summary` (description HTML stripped to the lead sentence), `published` (`YYYY-MM-DD HH:MM`, VN time), `url`.
- **Channel → category:** `category_for_channel(name)` strips accents and compares to the feed slug or slugified name (`#the-thao`, `#thể-thao`, `#gia-dinh`/`#doi-song` all match). `ask_model` sets the `default_category` ContextVar per message, so `get_news()` without category uses it even if the model forgets.
- Summarizing is done by the model from titles + summaries; no article pages are fetched.
- Excluded feeds (2026-10-29): `startup` (empty), `tin-xem-nhieu` (only 2021 articles).

## Tuning knobs

- `HISTORY_LEN = 20`, `MAX_TOOL_ROUNDS = 6` – `config.py`
- `temperature 0.3` – `agent.py`
- `MAX_ITEMS = 30` news cap, `MAX_AGE_DAYS = 3` – `tools/news/vnexpress.py`
- `NEWS_COUNT = 5` and the brief `PROMPT` – `morning.py`
- `MORNING_TIME`, `TIMEZONE`, `MORNING_CHANNEL_ID` – `.env`
- `OLLAMA_THINK=false` – passes `think=False` to Ollama

## Trade-offs

- **Folder per tool group, flat tool list for the model** – easy to add groups; no routing or sub-agents. Fine while total tools stay small (~6 now); a 9B model degrades with many tools, then consider per-group enabling.
- **Plain modules, no classes** – a group is just `TOOLS` + `SPECS`.
- **Global lock** – fine for one user; per-channel locks if it ever serves more.
- **Only final Q/A stored in history** – keeps context small, but model forgets tool results between turns and re-queries.
- **No caching** – Trello lists/cards and RSS re-fetched on each tool call.
- **In-memory history** – lost on restart; acceptable for personal use.
