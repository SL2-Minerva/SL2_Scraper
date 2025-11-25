import asyncio
import os
import scraper.tiktok_test as tiktokScraperTest

# from TikTokApi import TikTokApi


# RUN: python install -r requirements.txt
# RUN: python3 playwright install


async def run():
    # ms_token = "bB5FIqqY8dWy4BTdm_9XV1p36IuFPf6TUvTem28RVKZtVtDN5Li_Jn05PcsxA4D95Zawh1lYks8aUW8DfEtMPgHW3tPmcpSYmO5PnvrJYehoAvH9wofR76UyRQQBw87KF4qbwPUcvvDbLw=="
    print("testing...")

    await tiktokScraperTest.run_one_post_test()

    print("done")


asyncio.run(run())
