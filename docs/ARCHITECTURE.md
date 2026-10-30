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
| Weather | `requests` against Open-Meteo forecast + geocoding APIs | free, no API key, hourly data |
| Config | `python-dotenv` reading `.env` | |

## Shape: one agent, tool groups

```
self_agent/
  agent.py  ──uses──▶  tools/__init__.py (registry: TOOLS, TOOL_SPECS, run_tool)
                          ├── trello/   TOOLS + SPECS
                          ├── news/     TOOLS + SPECS
                          └── weather/  TOOLS + SPECS
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
              gather(get_weather days=2, get_news "Tin nổi bật" ×5, list_cards)   ← code, not model
              chat([system_prompt, PROMPT + JSON data], no tools) → greeting / weather / news / tasks
              history[channel] += answer (so the user can ask follow-ups)
            model error → still sends a short greeting with the error

Local test page (`python -m self_agent.web`, 127.0.0.1:8000)
  └─ GET / → web.html │ POST /chat {text, channel}
       ├─ "!morning" → morning_brief(None)              (not stored)
       └─ ask_model(None, text, channel, trace)          (no history in, nothing saved)
          → {answer, trace: [{tool, args, result}], seconds}
```

## Components

- **`config.py`** – env vars read at import; required ones use `os.environ[...]` so missing values crash at startup. Tuning constants.
- **`agent.py`** – `chat()` single Ollama call; `system_prompt(news_category)` (Vietnamese; today's date + weekday; never invent names; on news, summarize as bullets with links, only from tool output; on weather, resolve relative dates and answer a specific time from the nearest hourly slot; channel's news category if any); `ask_model()` tool loop; `history`.
- **`morning.py`** – `morning_brief()`: data fetched deterministically in code (a 9B model may skip tool calls), model only formats, following a full template with icons for all sections (rules kept outside the template so the model doesn't copy them; leftover `--- KHUÔN ---` marker lines are stripped in code): greeting with date, weather today + tomorrow (Trời with `icon` from data / Nhiệt độ / Mưa / UV / Lời khuyên per day), weekday + date of today/tomorrow computed in code (`_day`) since the model miscounts weekdays, 3–5 impactful news with links, Trello: overdue / due today first, then cards grouped by column, done cards skipped.
- **`discord_bot.py`** – client, `on_message` filtering (DMs always allowed), `!reset`, `!morning`, chunked replies sent with `suppress_embeds=True` (links stay clickable, no preview cards), global `lock`, `morning_job`, `run()`.
- **`web.py` / `web.html`** – stdlib `ThreadingHTTPServer` on 127.0.0.1; coroutines run on one background event loop via `run_coroutine_threadsafe`; page renders Discord-style markdown (bold, italic, bullets, links; HTML escaped) and a collapsible tool trace. Enter sends (IME-safe for Vietnamese typing).
- **`tools/__init__.py`** – `GROUPS = [trello, news, weather]`, merges `TOOLS` and `TOOL_SPECS`. `run_tool` runs a tool via `asyncio.to_thread` and always returns a JSON string, mapping errors to `{"error": ...}`:
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

**Weather** (`tools/weather/open_meteo.py`)

| Tool | Args | Source |
|---|---|---|
| `get_weather` | `location?` (default `WEATHER_LOCATION`), `date?` (`YYYY-MM-DD`, default today), `days?` (default 1, clamped 1–7) | `GET geocoding-api.open-meteo.com/v1/search` → `GET api.open-meteo.com/v1/forecast` |

- Place name → coordinates via Open-Meteo geocoding (`language=vi`, first result; Vietnamese with or without accents works, foreign cities too). `timezone=auto` so hours are local to the place.
- Returns `location` (`name, country`) and per day: `weather` (WMO code → Vietnamese via `WMO`), `icon` (emoji by WMO group, `_icon`), `temp_min/max`, `rain_mm`, `rain_chance_max_pct`, `uv_max`, `wind_max_kmh`, `sunrise/sunset`, and `hourly` slots (`time`, `weather`, `temp`, `feels_like`, `humidity_pct`, `rain_chance_pct`, `rain_mm`, `wind_kmh`).
- Hourly slots: every hour when `days=1`, every 3 hours when more (keeps context small).
- Unknown place → `LookupError` (bot asks again); bad date format → `ValueError`; date beyond ~15 days → Open-Meteo 400 with reason.

## Tuning knobs

- `HISTORY_LEN = 20`, `MAX_TOOL_ROUNDS = 6` – `config.py`
- `temperature 0.3`, `num_ctx` = `OLLAMA_NUM_CTX` (default 8192) – `agent.py` / `.env`
- `MAX_ITEMS = 30` news cap, `MAX_AGE_DAYS = 3` – `tools/news/vnexpress.py`
- `MAX_DAYS = 7`, hourly step 1 h / 3 h – `tools/weather/open_meteo.py`
- `NEWS_COUNT = 5` and the brief `PROMPT` – `morning.py`
- `MORNING_TIME`, `TIMEZONE`, `MORNING_CHANNEL_ID`, `WEATHER_LOCATION` – `.env`
- `OLLAMA_THINK=false` – passes `think=False` to Ollama

## Trade-offs

- **Folder per tool group, flat tool list for the model** – easy to add groups; no routing or sub-agents. Fine while total tools stay small (7 now); a 9B model degrades with many tools, then consider per-group enabling.
- **Plain modules, no classes** – a group is just `TOOLS` + `SPECS`.
- **Global lock** – fine for one user; per-channel locks if it ever serves more.
- **Only final Q/A stored in history** – keeps context small, but model forgets tool results between turns and re-queries.
- **No caching** – Trello lists/cards, RSS and forecasts re-fetched on each tool call.
- **In-memory history** – lost on restart; acceptable for personal use.
