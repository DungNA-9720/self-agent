"""Cấu hình, đọc từ file .env."""

import os
from datetime import time
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
ALLOWED_USER_ID = int(os.environ["DISCORD_USER_ID"])  # chỉ trả lời người này
# Các kênh bot trả lời, cách nhau bằng dấu phẩy; rỗng = mọi kênh bot thấy được
CHANNEL_IDS = [int(x) for x in os.getenv("DISCORD_CHANNEL_ID", "").split(",") if x.strip()]
TRELLO_KEY = os.environ["TRELLO_API_KEY"]
TRELLO_TOKEN = os.environ["TRELLO_TOKEN"]
TRELLO_BOARD = os.environ["TRELLO_BOARD_ID"]
MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:9b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
THINK = os.getenv("OLLAMA_THINK", "").lower()  # "false" để tắt chế độ suy nghĩ (trả lời nhanh hơn)

def _morning_time():
    """'08:00' theo TIMEZONE -> datetime.time có múi giờ; rỗng = tắt bản tin buổi sáng."""
    raw = os.getenv("MORNING_TIME", "08:00").strip()
    if not raw:
        return None
    h, m = map(int, raw.split(":"))
    return time(h, m, tzinfo=ZoneInfo(os.getenv("TIMEZONE") or "Asia/Ho_Chi_Minh"))


MORNING_TIME = _morning_time()
# Kênh nhận bản tin buổi sáng; rỗng = kênh đầu tiên trong DISCORD_CHANNEL_ID;
# cả hai rỗng = gửi tin nhắn riêng (DM) cho người dùng
MORNING_CHANNEL_ID = int(os.getenv("MORNING_CHANNEL_ID") or 0) or next(iter(CHANNEL_IDS), 0)

# Địa điểm mặc định cho dự báo thời tiết và bản tin buổi sáng
WEATHER_LOCATION = os.getenv("WEATHER_LOCATION") or "Hà Nội"

HISTORY_LEN = 20     # số tin nhắn gần nhất model được nhớ
MAX_TOOL_ROUNDS = 6    # số vòng gọi tool tối đa cho mỗi tin nhắn
TRELLO_API = "https://api.trello.com/1"
