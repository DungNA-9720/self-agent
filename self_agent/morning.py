"""Bản tin buổi sáng: chào ngày mới, thời tiết, tin nổi bật, tổng hợp công việc trên Trello."""

import asyncio
from datetime import date, timedelta

from .agent import chat, history, system_prompt, weekday_vi
from .tools import run_tool

NEWS_COUNT = 5

PROMPT = (
    "Viết bản tin buổi sáng gửi người dùng qua Discord, gồm 4 phần:\n"
    "Hôm nay là {today}, ngày mai là {tomorrow}; dùng đúng thứ và ngày này, không tự tính.\n"
    "1) Lời chào ngày mới ngắn, ấm áp, có thứ và ngày hôm nay.\n"
    "2) **Thời tiết** tại địa điểm trong dữ liệu, cho hôm nay và ngày mai. Mỗi thông tin một "
    "gạch đầu dòng riêng, không gộp nhiều thông tin vào một dòng, đúng khuôn sau:\n"
    "**Thời tiết <địa điểm>**\n"
    "**Hôm nay (<thứ>, <ngày/tháng>):**\n"
    "- Trời: <mô tả>\n"
    "- Nhiệt độ: <thấp>–<cao>°C\n"
    "- Mưa: khả năng <x>%, dễ mưa nhất khoảng <giờ>–<giờ> (ghi 'ít khả năng mưa' nếu dưới 30%)\n"
    "- UV: <chỉ số> (<thấp/trung bình/cao/rất cao>)\n"
    "- Lời khuyên: <1 câu ngắn: mang ô, chống nắng...>\n"
    "**Ngày mai (<thứ>, <ngày/tháng>):**\n"
    "<5 gạch đầu dòng như trên>\n"
    "3) **Tin nổi bật**: 3-5 tin có sức ảnh hưởng nhất trong dữ liệu tin, "
    "mỗi tin 1 dòng tóm tắt kèm link.\n"
    "4) **Công việc**: trước tiên một dòng 'Quá hạn' và một dòng 'Đến hạn hôm nay' "
    "(ghi 'không có' nếu trống); sau đó liệt kê các thẻ còn lại, nhóm dưới tên từng cột. "
    "Bỏ qua thẻ đã xong (done=true).\n"
    "Chỉ dùng dữ liệu bên dưới, không bịa. Phần nào dữ liệu báo lỗi thì nói ngắn gọn là "
    "chưa lấy được.\n\n"
    "Dữ liệu thời tiết (JSON): {weather}\n\n"
    "Dữ liệu tin (JSON): {news}\n\n"
    "Dữ liệu thẻ Trello (JSON): {cards}"
)


def _day(d):
    return f"{weekday_vi(d)}, {d:%d/%m/%Y}"  # model 9B hay tính sai thứ nên đưa sẵn


async def morning_brief(channel_id):
    """Lấy dữ liệu bằng code (không phụ thuộc model tự gọi tool) rồi nhờ model viết bản tin."""
    today = date.today()
    weather, news, cards = await asyncio.gather(
        run_tool("get_weather", {"days": 2}),  # hôm nay + ngày mai
        run_tool("get_news", {"category": "Tin nổi bật", "limit": NEWS_COUNT}),
        run_tool("list_cards", {}),
    )
    msg = await chat([
        {"role": "system", "content": system_prompt()},
        {"role": "user", "content": PROMPT.format(
            today=_day(today), tomorrow=_day(today + timedelta(days=1)),
            weather=weather, news=news, cards=cards,
        )},
    ])
    answer = (msg.content or "").strip() or "Chào buổi sáng! (Model không viết được bản tin.)"
    # Lưu bản tin vào lịch sử để người dùng hỏi tiếp ("chi tiết tin số 2"); None = không lưu
    if channel_id is not None:
        history[channel_id].append({"role": "assistant", "content": answer})
    return answer
