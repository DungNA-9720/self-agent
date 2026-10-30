"""Bản tin buổi sáng: chào ngày mới, thời tiết, tin nổi bật, tổng hợp công việc trên Trello."""

import asyncio
from datetime import date, timedelta

from .agent import chat, history, system_prompt, weekday_vi
from .tools import run_tool

NEWS_COUNT = 5

# Khuôn đầy đủ cả 4 phần: model 9B bắt chước khuôn rất sát, phần nào thiếu icon/gạch đầu
# dòng trong khuôn thì nó cũng bỏ luôn.
PROMPT = (
    "Viết bản tin buổi sáng gửi người dùng qua Discord.\n"
    "Hôm nay là {today}, ngày mai là {tomorrow}; dùng đúng thứ và ngày này, không tự tính.\n"
    "Trình bày ĐÚNG khuôn dưới đây, giữ nguyên icon, chữ đậm và gạch đầu dòng; mỗi thông tin "
    "một dòng riêng, không gộp; thay phần <...> bằng dữ liệu.\n\n"
    "--- KHUÔN ---\n"
    "☀️ **Chào buổi sáng! Hôm nay là <thứ>, <ngày/tháng/năm>**\n"
    "<1 câu chúc ngắn, ấm áp>\n\n"
    "🌦️ **Thời tiết <địa điểm>**\n"
    "📅 **Hôm nay (<thứ>, <ngày/tháng>)**\n"
    "- <icon> Trời: <mô tả>\n"
    "- 🌡️ Nhiệt độ: <thấp>–<cao>°C\n"
    "- ☔ Mưa: <khả năng mưa>\n"
    "- 🔆 UV: <chỉ số> (<mức>)\n"
    "- 💡 Lời khuyên: <lời khuyên>\n\n"
    "📅 **Ngày mai (<thứ>, <ngày/tháng>)**\n"
    "<5 dòng giống hệt hôm nay>\n\n"
    "📰 **Tin nổi bật**\n"
    "- 📌 **<tiêu đề>**: <tóm tắt> 🔗 <link>\n"
    "<các tin khác, mỗi tin một dòng như trên>\n\n"
    "📋 **Công việc**\n"
    "- ⚠️ Quá hạn: <tên thẻ, hoặc 'không có'>\n"
    "- ⏰ Đến hạn hôm nay: <tên thẻ, hoặc 'không có'>\n"
    "🗂️ **<tên cột>**\n"
    "- <tên thẻ> <(hạn ngày/tháng) nếu có>\n"
    "<các cột khác như trên>\n\n"
    "💪 <1 câu kết ngắn>\n"
    "--- HẾT KHUÔN ---\n\n"
    "Quy tắc điền (không chép quy tắc vào bản tin):\n"
    "- <icon>: lấy đúng trường icon của ngày đó trong dữ liệu thời tiết.\n"
    "- <khả năng mưa>: 'khả năng X%, dễ mưa nhất khoảng HH:MM–HH:MM' theo các mốc giờ; "
    "nếu dưới 30% thì ghi 'ít khả năng mưa (X%)'.\n"
    "- <mức> UV: dưới 3 thấp, 3-5 trung bình, 6-7 cao, 8-10 rất cao, từ 11 cực cao.\n"
    "- <lời khuyên>: 1 câu ngắn hợp với mưa/nắng/UV của ngày đó.\n"
    "- Tin: chọn 3-5 tin có sức ảnh hưởng nhất; <tóm tắt> tối đa 20 từ.\n"
    "- Công việc: chỉ thẻ chưa xong (done=false); bỏ cột không còn thẻ; thẻ không có hạn "
    "thì chỉ ghi tên.\n"
    "- Chỉ dùng dữ liệu bên dưới, không bịa. Phần nào dữ liệu báo lỗi thì ghi một dòng ngắn "
    "là chưa lấy được.\n\n"
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
    # Model đôi khi chép cả dòng đánh dấu khuôn "--- KHUÔN ---" / "--- HẾT KHUÔN ---"
    text = "\n".join(l for l in (msg.content or "").splitlines() if "KHUÔN ---" not in l)
    answer = text.strip() or "Chào buổi sáng! (Model không viết được bản tin.)"
    # Lưu bản tin vào lịch sử để người dùng hỏi tiếp ("chi tiết tin số 2"); None = không lưu
    if channel_id is not None:
        history[channel_id].append({"role": "assistant", "content": answer})
    return answer
