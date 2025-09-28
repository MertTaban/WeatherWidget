import asyncio

from weather_service import fetch_current_weather


async def main():
    data = await fetch_current_weather(41.0082, 28.9784)  # İstanbul
    print(data)


if __name__ == "__main__":
    asyncio.run(main())
