# Spec

Documented from existing code (2026-10-29). Describes what the bot does today.

## Goal

Let one person manage a single Trello board by chatting in Vietnamese on Discord,
using a local LLM (Ollama) so no conversation data goes to a cloud model.

## User stories (MVP, implemented)

1. **Ask what columns exist.** Given the bot is running, when I ask about columns, it lists the board's list names.
2. **See tasks.** When I ask for cards (optionally in one column), it lists card name, column, due date, done flag, URL.
3. **Create task.** When I ask to add a card with a column (and optional description / due date `YYYY-MM-DD`), a card is created and the bot returns its link.
4. **Move task.** When I name a card (full or partial) and a target column, the card moves there.
5. **Comment.** When I name a card and text, a comment is added.
6. **Ambiguity handling.** If a name matches several cards/columns or none, the bot asks me instead of guessing.
7. **Relative dates.** Bot knows today's date and weekday, so "hạn thứ 6" resolves to a real date.
8. **Privacy.** Bot ignores every user except `DISCORD_USER_ID`, ignores other bots, and (optionally) other channels.
9. **Reset.** `!reset` clears conversation memory for the channel.
10. **Long replies.** Replies over Discord's 2000-char limit are split into 1900-char chunks.

## Out of scope / later

- Multiple boards or multiple users
- Delete / archive / rename cards, edit due dates, checklists, labels, members
- Persistent history across restarts
- Slash commands
