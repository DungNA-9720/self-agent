"""Nhóm tool Trello: xem cột/thẻ, tạo, chuyển, bình luận."""

from ..common import s, spec
from .api import add_comment, create_card, list_cards, list_columns, move_card

TOOLS = {
    "list_columns": list_columns,
    "list_cards": list_cards,
    "create_card": create_card,
    "move_card": move_card,
    "add_comment": add_comment,
}

SPECS = [
    spec("list_columns", "Liệt kê tên các cột (danh sách) trên bảng Trello."),
    spec(
        "list_cards", "Liệt kê các thẻ công việc trên bảng, có thể lọc theo một cột.",
        {"column": s("Tên cột để lọc. Bỏ trống để lấy tất cả thẻ.")},
    ),
    spec(
        "create_card", "Tạo một thẻ công việc mới trong một cột.",
        {
            "name": s("Tiêu đề thẻ"),
            "column": s("Tên cột sẽ chứa thẻ"),
            "description": s("Mô tả chi tiết (không bắt buộc)"),
            "due": s("Hạn chót dạng YYYY-MM-DD (không bắt buộc)"),
        },
        ["name", "column"],
    ),
    spec(
        "move_card", "Chuyển một thẻ sang cột khác (ví dụ sang cột Done khi xong việc).",
        {"card": s("Tên (hoặc một phần tên) của thẻ"), "column": s("Tên cột đích")},
        ["card", "column"],
    ),
    spec(
        "add_comment", "Thêm bình luận vào một thẻ.",
        {"card": s("Tên (hoặc một phần tên) của thẻ"), "text": s("Nội dung bình luận")},
        ["card", "text"],
    ),
]
