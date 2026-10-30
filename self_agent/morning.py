"""Bản tin buổi sáng: chào ngày mới, tin nổi bật, tổng hợp công việc trên Trello."""

import asyncio

from .agent import chat, history, system_prompt
from .tools import run_tool

NEWS_COUNT = 5

PROMPT = (
    "Viết bản tin buổi sáng gửi người dùng qua Discord, gồm 3 phần:\n"
    "1) Lời chào ngày mới ngắn, ấm áp, có thứ và ngày hôm nay.\n"
    "2) **Tin nổi bật**: 3-5 tin có sức ảnh hưởng nhất trong dữ liệu tin, "
    "mỗi tin 1 dòng tóm tắt kèm link.\n"
    "3) **Công việc**: trước tiên một dòng 'Quá hạn' và một dòng 'Đến hạn hôm nay' "
    "(ghi 'không có' nếu trống); sau đó liệt kê các thẻ còn lại, nhóm dưới tên từng cột. "
    "Bỏ qua thẻ đã xong (done=true).\n"
    "Chỉ dùng dữ liệu bên dưới, không bịa. Phần nào dữ liệu báo lỗi thì nói ngắn gọn là "
    "chưa lấy được.\n\n"
    "Dữ liệu tin (JSON): {news}\n\n"
    "Dữ liệu thẻ Trello (JSON): {cards}"
)


async def morning_brief(channel_id):
    """Lấy dữ liệu bằng code (không phụ thuộc model tự gọi tool) rồi nhờ model viết bản tin."""
    news, cards = await asyncio.gather(
        run_tool("get_news", {"category": "Tin nổi bật", "limit": NEWS_COUNT}),
        run_tool("list_cards", {}),
    )
    msg = await chat([
        {"role": "system", "content": system_prompt()},
        {"role": "user", "content": PROMPT.format(news=news, cards=cards)},
    ])
    answer = (msg.content or "").strip() or "Chào buổi sáng! (Model không viết được bản tin.)"
    # Lưu bản tin vào lịch sử để người dùng hỏi tiếp ("chi tiết tin số 2")
    history[channel_id].append({"role": "assistant", "content": answer})
    return answer
