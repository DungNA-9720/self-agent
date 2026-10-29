# trello-agent

Personal Trello assistant on Discord, powered by a **local LLM via Ollama**.
You chat with the bot in Vietnamese (e.g. *"thêm việc gọi khách hàng vào cột To Do, hạn thứ 6"*);
the model calls Trello tools (list / create / move / comment) and replies.

- Single-user: bot only answers the Discord user set in `DISCORD_USER_ID`.
- Runs fully local except Discord + Trello APIs. No cloud LLM.
- Bot replies in Vietnamese (system prompt enforces it).

## Requirements

- [uv](https://docs.astral.sh/uv/) and Python 3.13 (`.python-version`; `pyproject.toml` allows >=3.10)
- [Ollama](https://ollama.com) running locally with a tool-calling model pulled, e.g. `ollama pull qwen3.5:9b`
- A Discord bot application with **Message Content Intent** enabled (Developer Portal → Bot)
- Trello API key + token (https://trello.com/power-ups/admin) and a board ID (the short code in the board URL)

## Quick start

```bash
uv sync                    # install dependencies into .venv
cp .env.example .env       # then fill in the values
ollama serve               # if not already running
uv run python -m trello_agent   # start the bot
```

Invite the bot to your server, then message it in the configured channel.

## Configuration (`.env`)

| Variable | Required | Meaning |
|---|---|---|
| `DISCORD_BOT_TOKEN` | yes | Discord bot token |
| `DISCORD_USER_ID` | yes | Only this user ID gets answers |
| `DISCORD_CHANNEL_ID` | no | Restrict to one channel; empty = any channel the bot sees |
| `TRELLO_API_KEY` | yes | Trello API key |
| `TRELLO_TOKEN` | yes | Trello user token |
| `TRELLO_BOARD_ID` | yes | Board to manage |
| `OLLAMA_MODEL` | no | Default `qwen3.5:9b`; must support tool calling |
| `OLLAMA_HOST` | no | Default `http://localhost:11434` |
| `OLLAMA_THINK` | no | `false` disables "thinking" for faster replies; leave empty if model errors |

`.env` holds secrets and is gitignored. Never commit it.

## Usage

Talk naturally. Examples:

- `có những cột nào?` – list columns
- `liệt kê việc trong To Do` – list cards in a column
- `thêm thẻ "Gọi khách hàng" vào To Do, hạn 2026-11-01` – create card
- `chuyển thẻ gọi khách hàng sang Done` – move card (partial names work)
- `comment vào thẻ gọi khách hàng: đã gọi xong` – add comment
- `!reset` – clear conversation history for this channel

## Project structure

```
trello_agent/
  __main__.py     entrypoint (`python -m trello_agent`)
  config.py       env vars + tuning constants
  trello.py       Trello REST helper, name lookup, the 5 tool functions
  tools.py        tool registry, JSON schemas for the model, run_tool error mapping
  agent.py        Ollama client, system prompt, history, tool-calling loop
  discord_bot.py  Discord client, message filtering, !reset, reply chunking
pyproject.toml    project metadata + dependencies
uv.lock           pinned dependency versions
.env.example      config template
docs/             spec, architecture, task tracking
.claude/agents/   Claude Code subagent definitions
CLAUDE.md         guide for Claude Code / maintainers
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for how it works and [docs/TASKS.md](docs/TASKS.md) for status and open work.
