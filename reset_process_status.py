import asyncio

import modules.file_handle as fileHandle


async def set_process_status(status="0", platform=""):
    try:
        await fileHandle.write_process_status(
            status=status, platform=platform)
    except Exception as e:
        print(f"error on set_process_status\n\n {e}")


async def main():
    await set_process_status(status="0", platform=fileHandle.process_twitter)
    await set_process_status(status="0", platform=fileHandle.process_pantip)
    await set_process_status(status="0", platform=fileHandle.process_tiktok)


asyncio.run(main())
