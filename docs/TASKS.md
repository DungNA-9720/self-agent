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
- [x] Refactor `bot.py` into `trello_agent/` package (config, trello, tools, agent, discord_bot); removed `bot.py` and `main.py` stub. Run with `uv run python -m trello_agent`.

## Open

- [ ] First git commit (repo has no commits yet). Check `git status` shows no `.env` before committing. — owner: user
- [ ] Add a small test for `_find` and `run_tool` error mapping (no network; monkeypatch `trello`). — backend-developer
- [ ] Optional: tools to archive card, edit due date, mark due complete. — architect → backend-developer
- [ ] Optional: persist `history` across restarts. — backend-developer

## Known issues / notes

- If `DISCORD_USER_ID` / tokens are missing, bot crashes at import with `KeyError` (intended: fail fast).
- Exceptions not caught in `run_tool` (e.g. unexpected `KeyError` in Trello response) bubble to `on_message` and show as "Lỗi khi gọi model: ...".
- Model must support tool calling; small models may loop and hit `MAX_TOOL_ROUNDS`.
