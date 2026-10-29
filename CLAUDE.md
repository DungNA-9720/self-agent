# CLAUDE.md

Guide for Claude Code and maintainers working in this repo.

## What this is

`trello-agent`: single-user Discord bot that manages one Trello board through a local Ollama model with tool calling. User chats in Vietnamese; bot replies in Vietnamese. Code lives in the `trello_agent/` package.

## Commands

```bash
uv sync                          # install deps
uv run python -m trello_agent    # run bot (needs .env, Ollama running)
uv add <pkg>                     # add dependency (updates pyproject.toml + uv.lock)
```

No tests, linter, or CI configured yet.

## Layout

Dependency direction: `config` ← `trello` ← `tools` ← `agent` ← `discord_bot` ← `__main__`. Keep it one-way.

- `trello_agent/config.py` – loads `.env`; required vars crash on import if missing
- `trello_agent/trello.py` – `trello()` HTTP helper, `_find` name lookup, tool functions
- `trello_agent/tools.py` – `TOOLS`, `TOOL_SPECS`, `run_tool`
- `trello_agent/agent.py` – Ollama client, `system_prompt`, `history`, `ask_model`
- `trello_agent/discord_bot.py` – Discord client, `on_message`, global `lock`, `run()`
- `trello_agent/__main__.py` – entrypoint
- `docs/SPEC.md` – user stories / scope
- `docs/ARCHITECTURE.md` – flow, components, trade-offs (read before changing code)
- `docs/TASKS.md` – done / open work, known issues (update when finishing a task)
- `.claude/agents/` – project subagents: architect, backend-developer, code-improver, functional-reviewer, docs-writer

## Conventions

- Code comments, docstrings, user-facing strings, tool descriptions and system prompt are **Vietnamese**. Keep it that way.
- Adding a Trello tool = write the function in `trello.py`, then add it to `TOOLS` and a `_spec(...)` to `TOOL_SPECS` in `tools.py`. Tool must return JSON-serializable data; raise `LookupError` for "not found / ambiguous" so `run_tool` turns it into a model-readable error.
- Resolve cards/columns by name with `_find`; never expose raw IDs to the model.
- Blocking I/O (`requests`) runs via `asyncio.to_thread` in `run_tool`; keep Discord handlers async.
- Don't split modules further until one grows a real reason to.

## Secrets

`.env` holds Discord + Trello tokens and is gitignored. Never print, commit, or copy its values. Use `.env.example` for new variables (add placeholder + comment there and a row in README).

## Keep docs in sync

When behavior, config, or tools change, update README.md, docs/ARCHITECTURE.md and docs/TASKS.md in the same change.
