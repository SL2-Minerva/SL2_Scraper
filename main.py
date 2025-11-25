

import asyncio
import scraper.pantip as pantipScraper
import scraper.twitter as twitterScraper
import scraper.tiktok as tiktokScraper
import driver.main as driverInstant


async def run():
    platform = driverInstant.get_platform_from_argv()

    print("Platform: " + platform)

    if platform == "all" or platform == "pantip":
        print("Pantip running...")

        await pantipScraper.run()

    if platform == "all" or platform == "twitter":
        print("Twitter running...")

        await twitterScraper.run()

    if platform == "all" or platform == "tiktok":
        print("Tiktok running...")

        await tiktokScraper.run()

asyncio.run(run())
