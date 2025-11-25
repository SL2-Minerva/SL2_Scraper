import asyncio
from scraper import pantip_with_api


async def run():
    await pantip_with_api.run()

asyncio.run(run())
