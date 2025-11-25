
import modules.file_handle as fileHandle


async def check_process_running():
    try:
        status = await fileHandle.read_process_status(
            platform=fileHandle.process_twitter)

        if status == "1":
            return True
        else:
            return False
    except Exception as e:
        message_err = f"Twitter\n\n error on check_process_status\n\n {e}"
        print(message_err)

        return False


async def set_process_status(status="0"):
    try:
        await fileHandle.write_process_status(
            status=status, platform=fileHandle.process_twitter)
    except Exception as e:
        message_err = f"Twitter\n\n error on set_process_status\n\n {e}"
        print(message_err)


async def run_test():
    if await check_process_running():
        print("Process is running.")
        await set_process_status("0")
    else:
        print("Process is not running.")
        await set_process_status("1")
