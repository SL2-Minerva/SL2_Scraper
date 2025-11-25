

import asyncio
import scraper.instartgram as instagramScraper


async def run():
    await instagramScraper.run()


asyncio.run(run())
