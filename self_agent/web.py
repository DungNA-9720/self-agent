"""Trang web test tạm: chat trực tiếp với agent, không qua Discord.

Không dùng và không lưu lịch sử: mỗi tin nhắn được trả lời độc lập.
Chạy:  uv run python -m self_agent.web [port]   rồi mở http://127.0.0.1:8000
"""

import asyncio
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .agent import ask_model
from .config import MODEL
from .morning import morning_brief

PAGE = (Path(__file__).parent / "web.html").read_bytes()

# Một event loop chạy nền cho mọi request: client Ollama (httpx) gắn với loop nên
# không tạo loop mới mỗi lần.
loop = asyncio.new_event_loop()
threading.Thread(target=loop.run_forever, daemon=True).start()


async def handle(text, channel_name):
    if text.strip().lower() == "!morning":
        return await morning_brief(None), []
    trace = []
    answer = await ask_model(None, text, channel_name, trace)
    return answer, trace


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path != "/":
            return self._send(404, b"not found", "text/plain")
        self._send(200, PAGE, "text/html; charset=utf-8")

    def do_POST(self):
        if self.path != "/chat":
            return self._send(404, b"not found", "text/plain")
        try:
            req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            text = str(req.get("text", "")).strip()
            if not text:
                raise ValueError("Tin nhắn trống.")
            start = time.monotonic()
            fut = asyncio.run_coroutine_threadsafe(
                handle(text, str(req.get("channel", ""))), loop)
            answer, trace = fut.result()
            out = {"answer": answer, "trace": trace, "seconds": round(time.monotonic() - start, 1)}
            code = 200
        except Exception as e:  # lỗi Ollama, tham số sai...
            out, code = {"error": f"{type(e).__name__}: {e}"}, 500
        self._send(code, json.dumps(out, ensure_ascii=False).encode(), "application/json")


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    # Chỉ nghe trên máy này: trang không có đăng nhập mà agent sửa được Trello
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Trang test: http://127.0.0.1:{port}  | model: {MODEL}  | Ctrl+C để dừng")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
