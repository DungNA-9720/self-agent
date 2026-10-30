"""Discord client: lọc tin nhắn, gọi model, trả lời, gửi bản tin buổi sáng."""

import asyncio

import discord
from discord.ext import tasks

from .agent import ask_model, history
from .config import (
    ALLOWED_USER_ID, CHANNEL_IDS, DISCORD_TOKEN, MODEL, MORNING_CHANNEL_ID, MORNING_TIME,
)
from .morning import morning_brief

intents = discord.Intents.default()
intents.message_content = True  # nhớ bật Message Content Intent trong Developer Portal
bot = discord.Client(intents=intents)
lock = asyncio.Lock()  # mỗi lúc chỉ một yêu cầu tới model


def chunks(text):
    """Discord giới hạn 2000 ký tự/tin."""
    return [text[i:i + 1900] for i in range(0, len(text), 1900)]


async def send_morning(channel):
    async with lock, channel.typing():
        try:
            text = await morning_brief(channel.id)
        except Exception as e:  # lỗi Ollama, mất kết nối...
            text = f"Chào buổi sáng! Chưa tạo được bản tin vì lỗi khi gọi model: {e}"
    for part in chunks(text):
        await channel.send(part, suppress_embeds=True)  # chỉ hiện link, không bung ô xem trước


async def morning_channel():
    if MORNING_CHANNEL_ID:
        return bot.get_channel(MORNING_CHANNEL_ID) or await bot.fetch_channel(MORNING_CHANNEL_ID)
    user = await bot.fetch_user(ALLOWED_USER_ID)
    return await user.create_dm()


if MORNING_TIME:
    @tasks.loop(time=MORNING_TIME)
    async def morning_job():
        try:  # loop sẽ dừng hẳn nếu để lọt exception, mất bản tin các ngày sau
            await send_morning(await morning_channel())
        except Exception as e:
            print(f"Lỗi bản tin buổi sáng: {e!r}")


@bot.event
async def on_ready():
    target = f"kênh {MORNING_CHANNEL_ID}" if MORNING_CHANNEL_ID else "DM"
    print(f"Đã đăng nhập: {bot.user} | model: {MODEL} | "
          f"bản tin sáng: {f'{MORNING_TIME} -> {target}' if MORNING_TIME else 'tắt'}")
    if MORNING_TIME and not morning_job.is_running():
        morning_job.start()


@bot.event
async def on_message(message):
    if message.author.bot or message.author.id != ALLOWED_USER_ID:
        return
    # Tin nhắn riêng (DM) luôn được trả lời, để hỏi tiếp bản tin sáng gửi qua DM
    if CHANNEL_IDS and message.guild and message.channel.id not in CHANNEL_IDS:
        return
    text = message.content.strip()
    if not text:
        return

    if text.lower() == "!reset":
        history[message.channel.id].clear()
        await message.reply("Đã xóa lịch sử hội thoại.", mention_author=False)
        return

    if text.lower() == "!morning":  # gửi bản tin buổi sáng ngay vào kênh này
        await send_morning(message.channel)
        return

    async with lock, message.channel.typing():
        try:
            # DM không có tên kênh
            channel_name = getattr(message.channel, "name", "") or ""
            answer = await ask_model(message.channel.id, text, channel_name)
        except Exception as e:  # lỗi Ollama, mất kết nối...
            answer = f"Lỗi khi gọi model: {e}"

    for part in chunks(answer):
        await message.reply(part, mention_author=False, suppress_embeds=True)


def run():
    bot.run(DISCORD_TOKEN)
