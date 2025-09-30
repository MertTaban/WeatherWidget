import asyncio
import socket
from typing import Any, Dict, List, Optional

import aiohttp

BASE_URL = "https://api.open-meteo.com/v1/forecast"

# Açıklama sözlüğü (kısaltılmış ama yeterli)
WEATHER_CODES: Dict[int, str] = {
    0: "Açık",
    1: "Genelde Açık",
    2: "Parçalı Bulutlu",
    3: "Kapalı",
    45: "Sisli",
    48: "Kırağılı Sis",
    51: "Hafif Çiseleme",
    53: "Orta Çiseleme",
    55: "Yoğun Çiseleme",
    56: "Hafif Donan Çiseleme",
    57: "Yoğun Donan Çiseleme",
    61: "Hafif Yağmur",
    63: "Orta Yağmur",
    65: "Kuvvetli Yağmur",
    66: "Hafif Donan Yağmur",
    67: "Kuvvetli Donan Yağmur",
    71: "Hafif Kar",
    73: "Orta Kar",
    75: "Yoğun Kar",
    77: "Kar Taneleri",
    80: "Hafif Sağanak",
    81: "Orta Sağanak",
    82: "Kuvvetli Sağanak",
    85: "Hafif Kar Sağ.",
    86: "Kuvvetli Kar Sağ.",
    95: "Gök Gürültülü",
    96: "Dolulu (Hafif)",
    99: "Dolulu (Kuvvetli)",
}


def describe_weather(code: Optional[int]) -> str:
    if code is None:
        return "Bilinmiyor"
    return WEATHER_CODES.get(code, f"Kod {code}")


def _build_url(lat: float, lon: float, forecast_days: int = 4) -> str:
    # timezone=auto ile yerel saatlere göre veri; hourly ve daily alanları eklendi.
    params = (
        f"latitude={lat}&longitude={lon}"
        f"&current_weather=true"
        f"&hourly=temperature_2m,weathercode,is_day"
        f"&daily=temperature_2m_min,temperature_2m_max,weathercode"
        f"&forecast_days={forecast_days}"
        f"&timeformat=iso8601&timezone=auto"
    )
    return f"{BASE_URL}?{params}"


async def _robust_session() -> aiohttp.ClientSession:
    connector = aiohttp.TCPConnector(family=socket.AF_INET, ssl=True)
    timeout = aiohttp.ClientTimeout(total=12)
    # trust_env=True ile kurumsal proxy değişkenlerini otomatik kullanır
    return aiohttp.ClientSession(timeout=timeout, connector=connector, trust_env=True)


async def fetch_weather_bundle(
    lat: float, lon: float, forecast_days: int = 4, retries: int = 2
) -> Optional[Dict[str, Any]]:
    """
    Tek istekle: current_weather + hourly + daily döndürür.
    Dönen yapı örneği:
    {
      "current_weather": {...},
      "hourly": {"time": [...], "temperature_2m": [...], "weathercode": [...], "is_day": [...]},
      "daily":  {"time": [...], "temperature_2m_min":[...], "temperature_2m_max":[...], "weathercode":[...] }
    }
    """
    url = _build_url(lat, lon, forecast_days=forecast_days)
    try:
        async with await _robust_session() as sess:
            for attempt in range(1, retries + 2):
                try:
                    async with sess.get(url) as resp:
                        if resp.status != 200:
                            print(f"[weather_service] HTTP {resp.status}")
                            return None
                        data = await resp.json()
                        # Beklediğimiz alanlar var mı?
                        if not data.get("current_weather"):
                            return None
                        return {
                            "current": data["current_weather"],
                            "hourly": data.get("hourly", {}),
                            "daily": data.get("daily", {}),
                        }
                except (
                    aiohttp.ClientConnectorError,
                    aiohttp.ClientConnectorDNSError,
                    asyncio.TimeoutError,
                ) as e:
                    print(
                        f"[weather_service] try {attempt}/{retries+1} failed: {type(e).__name__}"
                    )
                    if attempt >= retries + 1:
                        return None
                    await asyncio.sleep(1.5 * attempt)
                except RuntimeError as e:
                    print(f"[weather_service] runtime error: {e}")
                    return None
    except Exception as e:
        print(f"[weather_service] session create error: {e}")
        return None


# Eski API ile geriye dönük uyumluluk isteyen kısımlar varsa:
async def fetch_current_weather(lat: float, lon: float) -> Optional[dict]:
    bundle = await fetch_weather_bundle(lat, lon, forecast_days=2)
    return bundle["current"] if bundle else None
