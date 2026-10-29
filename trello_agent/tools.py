"""Đăng ký tool: schema gửi cho model và hàm chạy tool."""

import asyncio
import json

import requests

from .trello import add_comment, create_card, list_cards, list_columns, move_card

TOOLS = {
    "list_columns": list_columns,
    "list_cards": list_cards,
    "create_card": create_card,
    "move_card": move_card,
    "add_comment": add_comment,
}


def _spec(name, description, props=None, required=()):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": props or {},
                "required": list(required),
            },
        },
    }


def _s(desc):
    return {"type": "string", "description": desc}


TOOL_SPECS = [
    _spec("list_columns", "Liệt kê tên các cột (danh sách) trên bảng Trello."),
    _spec(
        "list_cards", "Liệt kê các thẻ công việc trên bảng, có thể lọc theo một cột.",
        {"column": _s("Tên cột để lọc. Bỏ trống để lấy tất cả thẻ.")},
    ),
    _spec(
        "create_card", "Tạo một thẻ công việc mới trong một cột.",
        {
            "name": _s("Tiêu đề thẻ"),
            "column": _s("Tên cột sẽ chứa thẻ"),
            "description": _s("Mô tả chi tiết (không bắt buộc)"),
            "due": _s("Hạn chót dạng YYYY-MM-DD (không bắt buộc)"),
        },
        ["name", "column"],
    ),
    _spec(
        "move_card", "Chuyển một thẻ sang cột khác (ví dụ sang cột Done khi xong việc).",
        {"card": _s("Tên (hoặc một phần tên) của thẻ"), "column": _s("Tên cột đích")},
        ["card", "column"],
    ),
    _spec(
        "add_comment", "Thêm bình luận vào một thẻ.",
        {"card": _s("Tên (hoặc một phần tên) của thẻ"), "text": _s("Nội dung bình luận")},
        ["card", "text"],
    ),
]


async def run_tool(name, args):
    """Chạy tool và luôn trả về chuỗi JSON (kể cả khi lỗi) để model đọc được."""
    fn = TOOLS.get(name)
    if fn is None:
        return json.dumps({"error": f"Không có tool tên {name}."}, ensure_ascii=False)
    try:
        if isinstance(args, str):
            args = json.loads(args or "{}")
        result = await asyncio.to_thread(fn, **(args or {}))
        return json.dumps(result, ensure_ascii=False)
    except LookupError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    except (TypeError, json.JSONDecodeError) as e:
        return json.dumps({"error": f"Tham số không hợp lệ: {e}"}, ensure_ascii=False)
    except requests.HTTPError as e:
        msg = f"Trello báo lỗi {e.response.status_code}: {e.response.text[:200]}"
        return json.dumps({"error": msg}, ensure_ascii=False)
    except requests.RequestException as e:
        return json.dumps({"error": f"Không kết nối được Trello: {e}"}, ensure_ascii=False)
