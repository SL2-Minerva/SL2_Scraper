
import requests

sl_bot_token = "8130711841:AAE14UCdPiEmkHjDUsLWuM2uYEs3jDHLY_U"
sl_pantip_bot_token = "7699996629:AAHExQkNinjLqfMFGIBV9nPNjW_TsXCll2g"
sl_x_bot_token = "8142385934:AAFO0bgkzD6VY-LMUl1fxbvrf320jzlz5MY"
sl_tiktok_bot_token = "7573483824:AAHNEaxn5U8QEbdMOihPQGUFUNT7ADM4EQI"

chat_id_private = 8138633772
chat_id_group_scraper_noti = -1002638286103
chat_id_pantip_work_process = -1002686967016
chat_id_x_work_process = -1002603938189
chat_id_tiktok_work_process = -1002457882846


version = "v. 4.3"


def send_message(message="", token="", chat_id=""):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"

        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"  # หรือ Markdown
        }

        r = requests.post(url, data=payload)

        return r.text
    except Exception as e:
        return None


def send_to_private(message=""):
    return send_message(
        message=f"{message}\n\n{version}", token=sl_bot_token, chat_id=chat_id_private)


def send_to_scraper_notify(message=""):
    return send_message(
        message=f"{message}\n\n{version}", token=sl_bot_token, chat_id=chat_id_group_scraper_noti)


def send_to_pantip_private(message=""):
    return send_message(
        message=f"{message}\n\n{version}", token=sl_pantip_bot_token, chat_id=chat_id_private)


def send_to_pantip_work_process(message=""):
    return send_message(
        message=f"{message}\n\n{version}", token=sl_pantip_bot_token, chat_id=chat_id_pantip_work_process)


def send_to_x_private(message=""):
    return send_message(
        message=f"{message}\n\n{version}", token=sl_x_bot_token, chat_id=chat_id_private)


def send_to_x_work_process(message=""):
    return send_message(
        message=f"{message}\n\n{version}", token=sl_x_bot_token, chat_id=chat_id_x_work_process)


def send_to_tiktok_private(message=""):
    return send_message(
        message=f"{message}\n\n{version}", token=sl_tiktok_bot_token, chat_id=chat_id_private)


def send_to_tiktok_work_process(message=""):
    return send_message(
        message=f"{message}\n\n{version}", token=sl_tiktok_bot_token, chat_id=chat_id_tiktok_work_process)
