# self-agent

Personal assistant on Discord, powered by a **local LLM via Ollama**. One agent, several tool groups:

- **Trello** – list / create / move / comment on cards of one board
- **News** – fetch and summarize VnExpress articles from the last 3 days via RSS (https://vnexpress.net/rss)
- **Weather** – daily and hourly forecast for any place from Open-Meteo (https://open-meteo.com, no API key)
- **Morning brief** – every day at 08:00 the bot sends a greeting, weather for today and tomorrow, top news (Tin nổi bật) and a summary of your Trello cards

You chat in Vietnamese (e.g. *"thêm việc gọi khách hàng vào cột To Do, hạn thứ 6"*, *"tóm tắt tin thể thao hôm nay"*);
the model calls tools and replies in Vietnamese.

- Single-user: bot only answers the Discord user set in `DISCORD_USER_ID`.
- Runs locally except Discord, Trello and VnExpress HTTP calls. No cloud LLM.

## Requirements

- [uv](https://docs.astral.sh/uv/) and Python 3.13 (`.python-version`; `pyproject.toml` allows >=3.10)
- [Ollama](https://ollama.com) running locally with a tool-calling model pulled, e.g. `ollama pull qwen3.5:9b`
- A Discord bot application with **Message Content Intent** enabled (Developer Portal → Bot)
- Trello API key + token (https://trello.com/power-ups/admin) and a board ID (the short code in the board URL)

## Quick start

```bash
uv sync                          # install dependencies into .venv
cp .env.example .env             # then fill in the values
ollama serve                     # if not already running
uv run python -m self_agent      # start the bot
```

Invite the bot to your server, then message it in the configured channel.

### Local test page (no Discord)

```bash
uv run python -m self_agent.web        # then open http://127.0.0.1:8000 (port: add a number)
```

Chat with the same agent and tools in the browser. **No memory**: every message is answered on its own, nothing is stored. Shows which tools were called (args + raw result) and response time. Fill "Tên kênh giả lập" (e.g. `the-thao`) to test news-by-channel; `!morning` shows the morning brief. Listens on 127.0.0.1 only (no login, and the agent can change Trello). Still needs `.env` and Ollama.

## Configuration (`.env`)

| Variable | Required | Meaning |
|---|---|---|
| `DISCORD_BOT_TOKEN` | yes | Discord bot token |
| `DISCORD_USER_ID` | yes | Only this user ID gets answers |
| `DISCORD_CHANNEL_ID` | no | Comma-separated channel IDs the bot answers in; empty = any channel the bot sees. DMs from you are always answered |
| `MORNING_TIME` | no | Morning brief time `HH:MM`, default `08:00`; empty = off |
| `TIMEZONE` | no | Timezone for `MORNING_TIME`, default `Asia/Ho_Chi_Minh` |
| `WEATHER_LOCATION` | no | Default place for weather questions and the morning brief, default `Hà Nội` |
| `MORNING_CHANNEL_ID` | no | Channel for the morning brief; empty = first ID in `DISCORD_CHANNEL_ID`; both empty = DM to you |
| `TRELLO_API_KEY` | yes | Trello API key |
| `TRELLO_TOKEN` | yes | Trello user token |
| `TRELLO_BOARD_ID` | yes | Board to manage |
| `OLLAMA_MODEL` | no | Default `qwen3.5:9b`; must support tool calling |
| `OLLAMA_HOST` | no | Default `http://localhost:11434` |
| `OLLAMA_NUM_CTX` | no | Context tokens per model call, default `8192` (Ollama's own default 4096 cuts off the morning brief) |
| `OLLAMA_THINK` | no | `false` disables "thinking" for faster replies; leave empty if model errors |

News and weather need no API key. `.env` holds secrets and is gitignored. Never commit it.

## Usage

Talk naturally. Examples:

- `có những cột nào?` – list columns
- `liệt kê việc trong To Do` – list cards in a column
- `thêm thẻ "Gọi khách hàng" vào To Do, hạn 2026-11-01` – create card
- `chuyển thẻ gọi khách hàng sang Done` – move card (partial names work)
- `comment vào thẻ gọi khách hàng: đã gọi xong` – add comment
- `có tin gì mới?` – summary of latest news
- `tóm tắt 5 tin kinh doanh` – news by category (Thời sự, Thế giới, Kinh doanh, Thể thao, Khoa học công nghệ, …)
- `3 giờ chiều mai ở Hà Nội có mưa không?` – hourly forecast at a specific time
- `thời tiết Đà Nẵng cuối tuần` – multi-day forecast for another place
- `!morning` – send the morning brief now, in this channel
- `!reset` – clear conversation history for this channel

**News channels:** name a Discord channel after a category (`#the-thao`, `#thể-thao`, `#kinh-doanh`, `#doi-song`, `#khoa-hoc-cong-nghe`, …). Asking `có tin gì mới?` there returns that category. Other channels default to "Tin mới nhất". Remember to add those channel IDs to `DISCORD_CHANNEL_ID` if it is set.

## Project structure

```
self_agent/
  __main__.py          entrypoint (`python -m self_agent`)
  config.py            env vars + tuning constants
  agent.py             the single agent: Ollama client, system prompt, history, tool loop
  morning.py           morning brief: fetch weather + news + Trello cards, model writes the message
  discord_bot.py       Discord client, message filtering, !reset / !morning, daily 08:00 job
  web.py, web.html     local test page: stateless chat with tool trace (stdlib http.server)
  tools/
    __init__.py        registry: merges all groups, run_tool error mapping
    common.py          shared helpers: spec(), s(), find_by_name()
    trello/
      __init__.py      TOOLS + SPECS for Trello
      api.py           Trello REST helper and tool functions
    news/
      __init__.py      TOOLS + SPECS for news
      vnexpress.py     VnExpress RSS categories, parser, get_news
    weather/
      __init__.py      TOOLS + SPECS for weather
      open_meteo.py    geocoding, forecast, WMO codes in Vietnamese, get_weather
pyproject.toml / uv.lock
.env.example           config template
docs/                  spec, architecture, task tracking
.claude/agents/        Claude Code subagent definitions
CLAUDE.md              guide for Claude Code / maintainers
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for how it works and [docs/TASKS.md](docs/TASKS.md) for status and open work.
