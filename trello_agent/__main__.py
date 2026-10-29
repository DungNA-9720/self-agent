"""
Cài đặt:  uv sync
Cấu hình: copy .env.example thành .env rồi điền thông tin
Chạy:     uv run python -m trello_agent
"""

from .discord_bot import run

run()
