"""Discord client: lọc tin nhắn, gọi model, trả lời."""

import asyncio

import discord

from .agent import ask_model, history
from .config import ALLOWED_USER_ID, CHANNEL_ID, DISCORD_TOKEN, MODEL

intents = discord.Intents.default()
intents.message_content = True  # nhớ bật Message Content Intent trong Developer Portal
bot = discord.Client(intents=intents)
lock = asyncio.Lock()


@bot.event
async def on_ready():
    print(f"Đã đăng nhập: {bot.user} | model: {MODEL}")


@bot.event
async def on_message(message):
    if message.author.bot or message.author.id != ALLOWED_USER_ID:
        return
    if CHANNEL_ID and message.channel.id != CHANNEL_ID:
        return
    text = message.content.strip()
    if not text:
        return

    if text.lower() == "!reset":
        history[message.channel.id].clear()
        await message.reply("Đã xóa lịch sử hội thoại.", mention_author=False)
        return

    async with lock, message.channel.typing():
        try:
            answer = await ask_model(message.channel.id, text)
        except Exception as e:  # lỗi Ollama, mất kết nối...
            answer = f"Lỗi khi gọi model: {e}"

    for i in range(0, len(answer), 1900):  # Discord giới hạn 2000 ký tự/tin
        await message.reply(answer[i:i + 1900], mention_author=False)


def run():
    bot.run(DISCORD_TOKEN)
