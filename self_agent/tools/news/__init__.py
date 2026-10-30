"""Nhóm tool tin tức: đọc RSS báo VnExpress."""

from ..common import s, spec
from .vnexpress import (
    CATEGORIES, MAX_AGE_DAYS, MAX_ITEMS, category_for_channel, default_category, get_news,
)

TOOLS = {"get_news": get_news}

SPECS = [
    spec(
        "get_news",
        f"Lấy tin tức trong {MAX_AGE_DAYS} ngày gần nhất từ RSS báo VnExpress "
        "(tiêu đề, tóm tắt, thời gian, link) để tổng hợp cho người dùng.",
        {
            "category": s(
                "Chuyên mục. Bỏ trống để dùng chuyên mục của kênh đang chat. Một trong: "
                + ", ".join(CATEGORIES)
            ),
            "limit": {
                "type": "integer",
                "description": f"Số tin cần lấy (1-{MAX_ITEMS}), mặc định 10",
            },
        },
    ),
]
