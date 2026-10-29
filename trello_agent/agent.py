"""Hội thoại với model Ollama: system prompt, lịch sử, vòng gọi tool."""

from collections import defaultdict, deque
from datetime import date

from ollama import AsyncClient

from .config import HISTORY_LEN, MAX_TOOL_ROUNDS, MODEL, OLLAMA_HOST, THINK
from .tools import TOOL_SPECS, run_tool

ollama = AsyncClient(host=OLLAMA_HOST)
history = defaultdict(lambda: deque(maxlen=HISTORY_LEN))


def system_prompt():
    today = date.today()
    weekday = "Chủ nhật" if today.isoweekday() == 7 else f"Thứ {today.isoweekday() + 1}"
    return (
        "Bạn là trợ lý quản lý công việc trên bảng Trello của người dùng. "
        f"Hôm nay là {weekday}, ngày {today:%Y-%m-%d}. "
        "Luôn trả lời bằng tiếng Việt, ngắn gọn. "
        "Khi cần xem hoặc thay đổi dữ liệu Trello, hãy gọi tool; không bao giờ tự bịa tên thẻ, "
        "tên cột hay kết quả. Nếu không chắc tên cột, gọi list_columns trước. "
        "Nếu tool báo lỗi hoặc có nhiều kết quả trùng tên, hãy hỏi lại người dùng."
    )


async def ask_model(channel_id, user_text):
    hist = history[channel_id]
    messages = [
        {"role": "system", "content": system_prompt()},
        *hist,
        {"role": "user", "content": user_text},
    ]
    extra = {"think": False} if THINK == "false" else {}

    answer = "Mình đã gọi tool quá nhiều lần mà chưa xong, bạn thử diễn đạt lại yêu cầu nhé."
    for _ in range(MAX_TOOL_ROUNDS):
        resp = await ollama.chat(
            model=MODEL,
            messages=messages,
            tools=TOOL_SPECS,
            options={"temperature": 0.3},
            **extra,
        )
        msg = resp.message
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
