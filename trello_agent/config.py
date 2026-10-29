"""Cấu hình, đọc từ file .env."""

import os

from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
ALLOWED_USER_ID = int(os.environ["DISCORD_USER_ID"])  # chỉ trả lời người này
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID") or 0)  # 0 = mọi kênh bot thấy được
TRELLO_KEY = os.environ["TRELLO_API_KEY"]
TRELLO_TOKEN = os.environ["TRELLO_TOKEN"]
TRELLO_BOARD = os.environ["TRELLO_BOARD_ID"]
MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:9b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
THINK = os.getenv("OLLAMA_THINK", "").lower()  # "false" để tắt chế độ suy nghĩ (trả lời nhanh hơn)

HISTORY_LEN = 20       # số tin nhắn gần nhất model được nhớ
MAX_TOOL_ROUNDS = 6    # số vòng gọi tool tối đa cho mỗi tin nhắn
TRELLO_API = "https://api.trello.com/1"
