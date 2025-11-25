import json
import asyncio
import scraper.pantip_with_api_test as PantipWithApiTest


async def run():
    print("testing...")

    await PantipWithApiTest.run()

    print("done")


asyncio.run(run())
