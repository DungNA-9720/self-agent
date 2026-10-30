"""Nhóm tool thời tiết: dự báo theo ngày và theo giờ từ Open-Meteo."""

from ...config import WEATHER_LOCATION
from ..common import s, spec
from .open_meteo import MAX_DAYS, get_weather

TOOLS = {"get_weather": get_weather}

SPECS = [
    spec(
        "get_weather",
        "Dự báo thời tiết (Open-Meteo): tóm tắt từng ngày (nhiệt độ thấp/cao, mưa, UV, gió, "
        "mặt trời mọc/lặn) và từng mốc giờ (nhiệt độ, cảm giác, độ ẩm, khả năng mưa, gió). "
        "Dùng khi người dùng hỏi thời tiết, mưa, nắng, nhiệt độ, kể cả tại một giờ cụ thể.",
        {
            "location": s(f"Tên thành phố/địa điểm. Bỏ trống = {WEATHER_LOCATION}."),
            "date": s("Ngày bắt đầu dạng YYYY-MM-DD (tối đa 15 ngày tới). Bỏ trống = hôm nay."),
            "days": {
                "type": "integer",
                "description": f"Số ngày cần dự báo (1-{MAX_DAYS}), mặc định 1. "
                               "Hỏi 1 ngày được dữ liệu từng giờ; nhiều ngày thì mỗi 3 giờ.",
            },
        },
    ),
]
