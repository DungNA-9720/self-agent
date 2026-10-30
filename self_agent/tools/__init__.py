"""Gom mọi nhóm tool (mỗi nhóm một folder) và chạy tool cho agent.

Thêm nhóm mới: tạo folder có TOOLS + SPECS trong __init__.py, rồi thêm vào GROUPS.
"""

import asyncio
import json
import xml.etree.ElementTree as ET

import requests

from . import news, trello, weather

GROUPS = [trello, news, weather]

TOOLS = {name: fn for g in GROUPS for name, fn in g.TOOLS.items()}
TOOL_SPECS = [sp for g in GROUPS for sp in g.SPECS]


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
    except (TypeError, ValueError) as e:  # gồm cả json.JSONDecodeError
        return json.dumps({"error": f"Tham số không hợp lệ: {e}"}, ensure_ascii=False)
    except ET.ParseError as e:
        return json.dumps({"error": f"RSS trả về dữ liệu lỗi: {e}"}, ensure_ascii=False)
    except requests.HTTPError as e:
        msg = f"Dịch vụ báo lỗi {e.response.status_code}: {e.response.text[:200]}"
        return json.dumps({"error": msg}, ensure_ascii=False)
    except requests.RequestException as e:
        # ponytail: không in {e} vì URL Trello chứa key/token trong query
        return json.dumps({"error": f"Không kết nối được dịch vụ ({type(e).__name__})."},
                          ensure_ascii=False)
