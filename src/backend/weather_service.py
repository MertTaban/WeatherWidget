from typing import Dict, Optional

import aiohttp

OPEN_METEO_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude={lat}&longitude={lon}&current_weather=true"
)

WEATHER_CODES: Dict[int, str] = {
    0: "Açık",
    1: "Genelde Açık",
    2: "Parçalı Bulutlu",
    3: "Kapalı",
    45: "Sisli",
    61: "Hafif Yağmur",
    63: "Orta Yağmur",
    65: "Kuvvetli Yağmur",
    71: "Hafif Kar",
    73: "Orta Kar",
    75: "Yoğun Kar",
    80: "Hafif Sağanak",
    81: "Orta Sağanak",
    82: "Kuvvetli Sağanak",
    95: "Gök Gürültülü Fırtına",
}


def describe_weather(code: Optional[int]) -> str:
    if code is None:
        return "Bilinmiyor"
    return WEATHER_CODES.get(code, f"Kod {code}")


async def fetch_current_weather(
    lat: float, lon: float, timeout_s: int = 10
) -> Optional[dict]:
    url = OPEN_METEO_URL.format(lat=lat, lon=lon)
    timeout = aiohttp.ClientTimeout(total=timeout_s)
    async with aiohttp.ClientSession(timeout=timeout) as sess:
        async with sess.get(url) as resp:
            if resp.status != 200:
                print(f"[weather_service] HTTP {resp.status}")
                return None
            data = await resp.json()
            return data.get("current_weather")
