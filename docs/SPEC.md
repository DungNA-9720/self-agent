# Spec

Documented from existing code (2026-10-29). Describes what the bot does today.

## Goal

One personal assistant on Discord, chatting in Vietnamese, using a local LLM (Ollama) so no
conversation data goes to a cloud model. Capabilities come from tool groups: manage a single
Trello board, and summarize VnExpress news.

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

11. **News summary.** When I ask for news (optionally a category like Thể thao, Kinh doanh, and a count), the bot fetches VnExpress RSS and replies with short bullet points, each with its link, using only feed content.
12. **Unknown category.** If the category matches none or several, the bot asks me instead of guessing.
13. **Fresh news only.** News older than 3 days is never returned.
14. **News by channel.** In a channel named after a category (e.g. `#the-thao`), asking "có tin gì mới?" returns that category's news, answered in that channel. In other channels the default is "Tin mới nhất"; naming a category still works anywhere.
15. **Morning brief.** Every day at 08:00 (configurable), the bot sends me (DM or a chosen channel) a greeting with the date, 3–5 impactful news items with links, and my Trello tasks: overdue and due today first, then by column. `!morning` sends it on demand. I can ask follow-ups about it.

## Out of scope / later

- Multiple boards or multiple users
- Delete / archive / rename cards, edit due dates, checklists, labels, members
- Persistent history across restarts
- Fetching full article text; other news sources
- Posting news into category channels automatically
- Slash commands
