import asyncio
from scraper import twitter_with_api


async def run():
    await twitter_with_api.run()

asyncio.run(run())
