

import asyncio
from scraper import twitter_with_api_test


async def run():
    print("testing...")
    await twitter_with_api_test.run()

    print("done")


asyncio.run(run())
