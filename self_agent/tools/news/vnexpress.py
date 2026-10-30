"""Đọc tin tức từ RSS của VnExpress (danh sách feed: https://vnexpress.net/rss)."""

import html
import re
import unicodedata
import xml.etree.ElementTree as ET
from contextvars import ContextVar
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import requests

from ..common import find_by_name

RSS_BASE = "https://vnexpress.net/rss"
MAX_ITEMS = 30     # giữ ngữ cảnh gọn cho model nhỏ
MAX_AGE_DAYS = 3   # chỉ lấy tin trong vòng N ngày gần nhất

# Chuyên mục mặc định theo kênh Discord đang chat; agent đặt giá trị trước khi gọi model.
# asyncio.to_thread copy context nên get_news (chạy trong thread) vẫn đọc được.
default_category = ContextVar("default_category", default="Tin mới nhất")

# Tên chuyên mục -> slug của feed.
# Bỏ "startup" (feed rỗng) và "tin-xem-nhieu" (chỉ toàn bài cũ từ 2021).
CATEGORIES = {
    "Tin mới nhất": "tin-moi-nhat",
    "Tin nổi bật": "tin-noi-bat",
    "Thời sự": "thoi-su",
    "Thế giới": "the-gioi",
    "Kinh doanh": "kinh-doanh",
    "Bất động sản": "bat-dong-san",
    "Khoa học công nghệ": "khoa-hoc-cong-nghe",
    "Giải trí": "giai-tri",
    "Thể thao": "the-thao",
    "Pháp luật": "phap-luat",
    "Giáo dục": "giao-duc",
    "Sức khỏe": "suc-khoe",
    "Đời sống": "gia-dinh",
    "Du lịch": "du-lich",
    "Xe": "oto-xe-may",
    "Góc nhìn": "goc-nhin",
    "Ý kiến": "y-kien",
    "Tâm sự": "tam-su",
    "Thư giãn": "thu-gian",
}


def _text(raw):
    """Bỏ thẻ HTML (ảnh, link) trong mô tả, chỉ giữ câu tóm tắt."""
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", raw or "")).split())


def _slugify(name):
    """'Thể thao' / '#thể-thao' -> 'the-thao' (bỏ dấu, đ -> d)."""
    s = unicodedata.normalize("NFD", name.lower().replace("đ", "d"))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return "-".join(re.findall(r"[a-z0-9]+", s))


def category_for_channel(channel_name):
    """Tên chuyên mục khớp với tên kênh Discord (theo slug feed hoặc tên bỏ dấu), không khớp -> None."""
    key = _slugify(channel_name or "")
    for name, slug in CATEGORIES.items():
        if key in (slug, _slugify(name)):
            return name
    return None


def _published(item):
    try:
        d = parsedate_to_datetime(item.findtext("pubDate"))
    except (TypeError, ValueError):
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def parse_rss(xml_bytes, limit, since):
    """Lấy tối đa `limit` tin đăng từ `since` trở đi; tin không có ngày bị bỏ."""
    out = []
    for i in ET.fromstring(xml_bytes).iter("item"):
        pub = _published(i)
        if pub is None or pub < since:
            continue
        out.append({
            "title": (i.findtext("title") or "").strip(),
            "summary": _text(i.findtext("description")),
            "published": pub.strftime("%Y-%m-%d %H:%M"),
            "url": i.findtext("link"),
        })
        if len(out) >= limit:
            break
    return out


def get_news(category=None, limit=10):
    category = category or default_category.get()
    if category in CATEGORIES.values():
        slug = category
    else:
        items = [{"name": k, "slug": v} for k, v in CATEGORIES.items()]
        slug = find_by_name(items, category, "chuyên mục")["slug"]
    limit = max(1, min(int(limit), MAX_ITEMS))
    since = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
    resp = requests.get(f"{RSS_BASE}/{slug}.rss", timeout=15)
    resp.raise_for_status()
    return parse_rss(resp.content, limit, since)


if __name__ == "__main__":
    sample = b"""<rss><channel><item><title>A</title>
    <description><![CDATA[<a href="x"><img src="y"></a></br>Sapo &amp; tin.]]></description>
    <pubDate>Thu, 29 Oct 2026 08:14:23 +0700</pubDate><link>https://vnexpress.net/a.html</link>
    </item>
    <item><title>B</title><pubDate>Wed, 28 Oct 2026 10:00:00 +0700</pubDate></item>
    <item><title>Old</title><pubDate>Sun, 25 Oct 2026 10:00:00 +0700</pubDate></item>
    <item><title>No date</title></item></channel></rss>"""
    since = datetime(2026, 10, 26, 8, tzinfo=timezone.utc)  # 3 ngày trước 2026-10-29 08:00 UTC
    got = parse_rss(sample, 5, since)
    assert got[0] == {"title": "A", "summary": "Sapo & tin.",
                      "published": "2026-10-29 08:14",
                      "url": "https://vnexpress.net/a.html"}, got[0]
    assert [g["title"] for g in got] == ["A", "B"], got
    assert len(parse_rss(sample, 1, since)) == 1
    assert category_for_channel("the-thao") == "Thể thao"
    assert category_for_channel("thể-thao") == "Thể thao"
    assert category_for_channel("doi-song") == "Đời sống"
    assert category_for_channel("gia-dinh") == "Đời sống"
    assert category_for_channel("khoa-hoc-cong-nghe") == "Khoa học công nghệ"
    assert category_for_channel("general") is None and category_for_channel("") is None
    print("ok")
