"""Dự báo thời tiết từ Open-Meteo (https://open-meteo.com/en/docs), không cần API key."""

import datetime as dt
from collections import defaultdict

import requests

from ...config import WEATHER_LOCATION

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
MAX_DAYS = 7  # Open-Meteo cho tới 16 ngày, giới hạn để giữ ngữ cảnh gọn

DAILY = ("weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,"
         "precipitation_probability_max,sunrise,sunset,uv_index_max,wind_speed_10m_max")
HOURLY = ("temperature_2m,apparent_temperature,relative_humidity_2m,"
          "precipitation_probability,precipitation,weather_code,wind_speed_10m")

# Mã thời tiết WMO -> mô tả tiếng Việt
WMO = {
    0: "Trời quang", 1: "Ít mây", 2: "Có mây", 3: "Nhiều mây, u ám",
    45: "Sương mù", 48: "Sương mù đóng băng",
    51: "Mưa phùn nhẹ", 53: "Mưa phùn", 55: "Mưa phùn dày",
    56: "Mưa phùn băng nhẹ", 57: "Mưa phùn băng",
    61: "Mưa nhỏ", 63: "Mưa vừa", 65: "Mưa to",
    66: "Mưa băng nhẹ", 67: "Mưa băng",
    71: "Tuyết nhẹ", 73: "Tuyết vừa", 75: "Tuyết dày", 77: "Hạt tuyết",
    80: "Mưa rào nhẹ", 81: "Mưa rào", 82: "Mưa rào rất to",
    85: "Mưa tuyết nhẹ", 86: "Mưa tuyết",
    95: "Dông", 96: "Dông kèm mưa đá nhỏ", 99: "Dông kèm mưa đá lớn",
}


def _wmo(code):
    return WMO.get(code, f"mã thời tiết {code}")


def geocode(name):
    resp = requests.get(GEOCODE_URL, params={"name": name, "count": 1, "language": "vi"}, timeout=15)
    resp.raise_for_status()
    results = resp.json().get("results")
    if not results:
        raise LookupError(f"Không tìm thấy địa điểm '{name}'. Hãy hỏi người dùng tên khác.")
    return results[0]


def summarize(data, step):
    """Gọn dữ liệu Open-Meteo: mỗi ngày một bản tóm tắt + các mốc giờ cách nhau `step` giờ."""
    hourly = defaultdict(list)
    h = data["hourly"]
    for i, t in enumerate(h["time"]):
        day, hour = t.split("T")
        if int(hour[:2]) % step:
            continue
        hourly[day].append({
            "time": hour,
            "weather": _wmo(h["weather_code"][i]),
            "temp": h["temperature_2m"][i],
            "feels_like": h["apparent_temperature"][i],
            "humidity_pct": h["relative_humidity_2m"][i],
            "rain_chance_pct": h["precipitation_probability"][i],
            "rain_mm": h["precipitation"][i],
            "wind_kmh": h["wind_speed_10m"][i],
        })
    d = data["daily"]
    return [
        {
            "date": day,
            "weather": _wmo(d["weather_code"][i]),
            "temp_min": d["temperature_2m_min"][i],
            "temp_max": d["temperature_2m_max"][i],
            "rain_mm": d["precipitation_sum"][i],
            "rain_chance_max_pct": d["precipitation_probability_max"][i],
            "uv_max": d["uv_index_max"][i],
            "wind_max_kmh": d["wind_speed_10m_max"][i],
            "sunrise": d["sunrise"][i].split("T")[1],
            "sunset": d["sunset"][i].split("T")[1],
            "hourly": hourly[day],
        }
        for i, day in enumerate(d["time"])
    ]


def get_weather(location=None, date=None, days=1):
    days = max(1, min(int(days), MAX_DAYS))
    place = geocode(location or WEATHER_LOCATION)
    params = {
        "latitude": place["latitude"], "longitude": place["longitude"],
        "timezone": "auto", "daily": DAILY, "hourly": HOURLY,
    }
    if date:
        start = dt.date.fromisoformat(date)  # sai định dạng -> ValueError -> "Tham số không hợp lệ"
        params.update(start_date=start.isoformat(),
                      end_date=(start + dt.timedelta(days=days - 1)).isoformat())
    else:
        params["forecast_days"] = days  # bắt đầu từ hôm nay theo giờ địa phương
    resp = requests.get(FORECAST_URL, params=params, timeout=15)
    resp.raise_for_status()
    name = ", ".join(x for x in (place.get("name"), place.get("admin1"), place.get("country")) if x)
    # 1 ngày: từng giờ; nhiều ngày: mỗi 3 giờ cho gọn
    return {"location": name, "days": summarize(resp.json(), 1 if days == 1 else 3)}


if __name__ == "__main__":
    sample = {
        "daily": {
            "time": ["2026-10-30"], "weather_code": [51], "temperature_2m_max": [29.9],
            "temperature_2m_min": [24.6], "precipitation_sum": [0.7],
            "precipitation_probability_max": [65], "sunrise": ["2026-10-30T05:58"],
            "sunset": ["2026-10-30T17:22"], "uv_index_max": [6.8], "wind_speed_10m_max": [11.9],
        },
        "hourly": {
            "time": [f"2026-10-30T{h:02d}:00" for h in range(24)],
            "temperature_2m": list(range(24)), "apparent_temperature": list(range(24)),
            "relative_humidity_2m": [90] * 24, "precipitation_probability": [20] * 24,
            "precipitation": [0.0] * 24, "weather_code": [2] * 24, "wind_speed_10m": [3.6] * 24,
        },
    }
    one = summarize(sample, 1)[0]
    assert one["weather"] == "Mưa phùn nhẹ" and one["sunrise"] == "05:58"
    assert len(one["hourly"]) == 24 and one["hourly"][15] == {
        "time": "15:00", "weather": "Có mây", "temp": 15, "feels_like": 15, "humidity_pct": 90,
        "rain_chance_pct": 20, "rain_mm": 0.0, "wind_kmh": 3.6}
    assert [x["time"] for x in summarize(sample, 3)[0]["hourly"]] == [
        "00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"]
    assert _wmo(1234) == "mã thời tiết 1234"
    print("ok")
