# CLAUDE.md

Guide for Claude Code and maintainers working in this repo.

## What this is

`self-agent`: single-user Discord bot with **one agent** (local Ollama model with tool calling) and several **tool groups**, each in its own folder under `self_agent/tools/`: Trello board management and VnExpress news (RSS). User chats in Vietnamese; bot replies in Vietnamese.

## Commands

```bash
uv sync                                    # install deps
uv run python -m self_agent                # run bot (needs .env, Ollama running)
uv run python -m self_agent.tools.news.vnexpress   # RSS parser self-test (needs dummy env vars, see below)
uv add <pkg>                               # add dependency (updates pyproject.toml + uv.lock)
```

`config.py` requires env vars at import. For offline checks set dummies:
`DISCORD_BOT_TOKEN=x DISCORD_USER_ID=1 TRELLO_API_KEY=x TRELLO_TOKEN=x TRELLO_BOARD_ID=x`.

No test suite, linter, or CI yet.

## Layout

Dependency direction: `config` ← `tools/<group>` ← `tools/__init__` ← `agent` ← `morning` ← `discord_bot` ← `__main__`. Keep it one-way; tool groups never import each other or `agent`.

- `self_agent/config.py` – loads `.env`; required vars crash on import if missing; `CHANNEL_IDS`, `MORNING_TIME` (tz-aware `time` or `None`), `MORNING_CHANNEL_ID`
- `self_agent/agent.py` – Ollama client, `chat()` (one model call), `system_prompt(news_category)`, `history`, `ask_model(channel_id, text, channel_name)`; sets news `default_category` from the channel name
- `self_agent/morning.py` – `morning_brief(channel_id)`: fetches news + cards in code via `run_tool`, model only writes the text
- `self_agent/discord_bot.py` – Discord client, `on_message` (`!reset`, `!morning`), global `lock`, daily `morning_job` (`discord.ext.tasks`), `run()`
- `self_agent/tools/__init__.py` – `GROUPS`, merged `TOOLS` / `TOOL_SPECS`, `run_tool`
- `self_agent/tools/common.py` – `spec()`, `s()`, `find_by_name()`
- `self_agent/tools/trello/` – `api.py` (functions), `__init__.py` (`TOOLS`, `SPECS`)
- `self_agent/tools/news/` – `vnexpress.py` (`CATEGORIES`, `MAX_AGE_DAYS=3`, `parse_rss`, `get_news`, `category_for_channel`, `default_category` ContextVar), `__init__.py` (`TOOLS`, `SPECS`)
- `docs/SPEC.md` – user stories / scope
- `docs/ARCHITECTURE.md` – flow, components, trade-offs (read before changing code)
- `docs/TASKS.md` – done / open work, known issues (update when finishing a task)
- `.claude/agents/` – project subagents: architect, backend-developer, code-improver, functional-reviewer, docs-writer

## Adding tools

- **New tool in existing group:** write the function in the group's module, add it to the group's `TOOLS` and a `spec(...)` to its `SPECS`.
- **New group:** create `self_agent/tools/<group>/` with an `__init__.py` exposing `TOOLS` (name → function) and `SPECS` (list of `spec(...)`), then add the module to `GROUPS` in `tools/__init__.py`. Tool names must be unique across groups.
- If the agent should know when to use it, add one sentence to `system_prompt()` in `agent.py`.

## Conventions

- Code comments, docstrings, user-facing strings, tool descriptions and system prompt are **Vietnamese**. Keep it that way.
- Tools return JSON-serializable data. Raise `LookupError` for "not found / ambiguous" and `ValueError`/`TypeError` for bad args; `run_tool` turns them into model-readable errors. HTTP errors via `requests.raise_for_status()`.
- Resolve things by name with `find_by_name`; never expose raw IDs to the model.
- Blocking I/O (`requests`) runs via `asyncio.to_thread` in `run_tool`; keep Discord handlers async.
- Never put exception text from `requests.RequestException` in tool output: Trello URLs carry key/token in the query string.
- Per-message state for tools (e.g. news `default_category`) goes through `ContextVar`: each Discord event runs in its own task and `asyncio.to_thread` copies the context, so values never leak between channels.
- Scheduled jobs must catch their own exceptions: an exception escaping a `tasks.loop` stops it for good.
- VnExpress CDN serves different cached versions of the same feed; don't write tests that compare article content between two fetches.

## Secrets

`.env` holds Discord + Trello tokens and is gitignored. Never print, commit, or copy its values. Use `.env.example` for new variables (add placeholder + comment there and a row in README).

## Keep docs in sync

When behavior, config, or tools change, update README.md, docs/ARCHITECTURE.md and docs/TASKS.md in the same change.
