# Tasks

Status as of 2026-10-29. Mark items `[x]` when done and add a one-line note.

## Done

- [x] Discord bot with single-user + channel filter
- [x] Ollama tool-calling loop with history and `!reset`
- [x] Trello tools: list columns, list cards, create, move, comment
- [x] Fuzzy name lookup with ambiguity errors
- [x] `.env.example` config template
- [x] Add `.env` to `.gitignore` (was missing; file holds real tokens)
- [x] README, CLAUDE.md, docs/SPEC.md, docs/ARCHITECTURE.md, docs/TASKS.md
- [x] Refactor `bot.py` into a package; removed `bot.py` and `main.py` stub.
- [x] First commit + push to github.com/DungNA-9720/self-agent (`.env` excluded).
- [x] News tool group: `get_news` from VnExpress RSS, 20 categories (2026-10-29). `startup` feed skipped (empty).
- [x] Restructure to `self_agent/`: one agent, tool groups in `tools/trello/` and `tools/news/`, shared helpers in `tools/common.py`. Run with `uv run python -m self_agent`.
- [x] News limited to last 3 days; dropped stale `tin-xem-nhieu` feed (2026-10-29).
- [x] News by channel: channel named after a category (`#the-thao`) defaults `get_news` to it. `DISCORD_CHANNEL_ID` accepts a comma-separated list; DMs always answered.
- [x] Morning brief at 08:00 (`MORNING_TIME`, `TIMEZONE`, `MORNING_CHANNEL_ID`): greeting + Tin nổi bật + Trello summary; `!morning` to trigger manually.
- [x] Weather tool group (Open-Meteo): `get_weather` daily + hourly for any place; weather today + tomorrow in the morning brief; `WEATHER_LOCATION` (2026-10-30).
- [x] Morning weather as one bullet per item (Trời, Nhiệt độ, Mưa, UV, Lời khuyên); weekday/date passed in from code after model wrote wrong weekday (2026-10-30).
- [x] Local test page `python -m self_agent.web`: stateless chat (no history), tool trace, simulated channel name, `!morning` (2026-10-30).
- [x] Morning brief layout: full icon template for all sections; weather icon computed from WMO code; fixed truncated brief by raising Ollama context to 8192 (`OLLAMA_NUM_CTX`, Ollama default 4096 hit `done_reason=length`) (2026-10-30).
- [x] Bot messages sent with `suppress_embeds=True`: news/Trello links show as plain links, no preview cards (2026-10-30).

## Open

- [ ] Add a small test for `find_by_name` and `run_tool` error mapping (no network; monkeypatch `api.trello`). — backend-developer
- [ ] Optional: tools to archive card, edit due date, mark due complete. — architect → backend-developer
- [ ] Optional: persist `history` across restarts. — backend-developer

## Known issues / notes

- If `DISCORD_USER_ID` / tokens are missing, bot crashes at import with `KeyError` (intended: fail fast).
- Exceptions not caught in `run_tool` (e.g. unexpected `KeyError` in Trello response) bubble to `on_message` and show as "Lỗi khi gọi model: ...".
- Model must support tool calling; small models may loop and hit `MAX_TOOL_ROUNDS`.
- VnExpress feeds can change or go empty (e.g. `startup`); `get_news` then returns `[]` and the model should say there is no news.
- If the bot is offline at 08:00, that day's brief is skipped (no catch-up). Use `!morning`.
- `MORNING_CHANNEL_ID` must also be in `DISCORD_CHANNEL_ID` (if that is set) to ask follow-ups there.
- Fixed 2026-10-30: brief went to DM when only `DISCORD_CHANNEL_ID` was set; now falls back to its first channel.
