import asyncio
import scraper.tiktok as tiktokScraper


async def run():
    await tiktokScraper.run()

asyncio.run(run())
