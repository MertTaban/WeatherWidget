import asyncio
import random
from typing import AsyncIterator


async def ticker() -> AsyncIterator[dict]:
    """Periyodik veri üreticisi (ör: sensör/HTTP)."""
    while True:
        await asyncio.sleep(1)
        yield {"value": random.randint(0, 100)}
