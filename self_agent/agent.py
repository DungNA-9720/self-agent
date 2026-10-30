"""Hội thoại với model Ollama: system prompt, lịch sử, vòng gọi tool."""

from collections import defaultdict, deque
from datetime import date

from ollama import AsyncClient

from .config import HISTORY_LEN, MAX_TOOL_ROUNDS, MODEL, OLLAMA_HOST, THINK
from .tools import TOOL_SPECS, run_tool
from .tools.news import category_for_channel, default_category

ollama = AsyncClient(host=OLLAMA_HOST)
history = defaultdict(lambda: deque(maxlen=HISTORY_LEN))


def system_prompt(news_category=None):
    today = date.today()
    weekday = "Chủ nhật" if today.isoweekday() == 7 else f"Thứ {today.isoweekday() + 1}"
    channel_hint = (
        f"Kênh chat hiện tại dành cho tin '{news_category}': khi người dùng hỏi tin tức mà "
        "không nói chuyên mục, gọi get_news không truyền category để lấy đúng chuyên mục này. "
        if news_category else ""
    )
    return (
        "Bạn là trợ lý quản lý công việc trên bảng Trello của người dùng, "
        "kiêm tổng hợp tin tức từ báo VnExpress. "
        f"Hôm nay là {weekday}, ngày {today:%Y-%m-%d}. "
        "Luôn trả lời bằng tiếng Việt, ngắn gọn. "
        "Khi cần xem hoặc thay đổi dữ liệu Trello, hãy gọi tool; không bao giờ tự bịa tên thẻ, "
        "tên cột hay kết quả. Nếu không chắc tên cột, gọi list_columns trước. "
        "Nếu tool báo lỗi hoặc có nhiều kết quả trùng tên, hãy hỏi lại người dùng. "
        "Khi người dùng hỏi tin tức, gọi get_news rồi tổng hợp thành gạch đầu dòng ngắn "
        "theo ý chính, mỗi tin kèm link; chỉ dùng nội dung tool trả về, không bịa thêm. "
        + channel_hint
    )


async def chat(messages, tools=None):
    """Một lượt gọi Ollama, trả về message của model."""
    extra = {"think": False} if THINK == "false" else {}
    resp = await ollama.chat(
        model=MODEL, messages=messages, tools=tools, options={"temperature": 0.3}, **extra,
    )
    return resp.message


async def ask_model(channel_id, user_text, channel_name=""):
    hist = history[channel_id]
    news_category = category_for_channel(channel_name)
    if news_category:
        default_category.set(news_category)  # chỉ ảnh hưởng task xử lý tin nhắn này
    messages = [
        {"role": "system", "content": system_prompt(news_category)},
        *hist,
        {"role": "user", "content": user_text},
    ]

    answer = "Mình đã gọi tool quá nhiều lần mà chưa xong, bạn thử diễn đạt lại yêu cầu nhé."
    for _ in range(MAX_TOOL_ROUNDS):
        msg = await chat(messages, TOOL_SPECS)
        if not msg.tool_calls:
            answer = (msg.content or "").strip() or "(Model không trả lời gì.)"
            break
        messages.append(msg)
        for call in msg.tool_calls:
            print(f"  -> tool {call.function.name}({call.function.arguments})")
            result = await run_tool(call.function.name, call.function.arguments)
            messages.append({"role": "tool", "content": result, "tool_name": call.function.name})

    # Chỉ lưu câu hỏi và câu trả lời cuối vào lịch sử để giữ ngữ cảnh gọn
    hist.append({"role": "user", "content": user_text})
    hist.append({"role": "assistant", "content": answer})
    return answer
