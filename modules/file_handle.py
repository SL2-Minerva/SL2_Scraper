from datetime import datetime

import modules.line_notify as lineNotify
import json
import os
import psutil
import csv


init_data = {"total_posts": 0, "total_comments": 0, "history": []}
example_data = {"datetime": "01/01/2023 10:10",
                "posts_count": 0, "comments_count": 0}

process_twitter = "twitter"
process_pantip = "pantip"
process_tiktok = "tiktok"
process_instagram = "instagram"


async def read_process_status(platform=process_twitter):
    data = None
    file_path = f"process/{platform}.txt"

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = file.read()

        return data
    except Exception as e:
        if "No such file or directory" in str(e):
            await write_process_status(status="0", platform=platform)
        else:
            message = f"{platform}\n\nError read process status:\n {e}."
            print(message)
            lineNotify.send_to_scraper_daily_data(message)

    return data


async def write_process_status(status="0", platform=process_twitter):
    file_path = f"process/{platform}.txt"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(status)
        print(f"Write file process status {platform} success.")
    except Exception as e:
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as file:
                file.write(status)

        except Exception as e:
            message = f"{platform}\n\nError on re-write process status:\n {e}."
            print(message)
            lineNotify.send_to_scraper_daily_data(message)


async def update_log_scraping(post_count=0, comment_count=0, platform="twitter", keyword=""):
    try:
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_date = datetime.now().strftime("%Y-%m-%d")

        file_path = f"logs/{platform}/{current_date}.json"

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                existing_data = json.load(file)
        except FileNotFoundError:
            existing_data = init_data

        new_data = {
            "keyword": f"{keyword}",
            "datetime": f"{current_datetime}",
            "posts_count": int(post_count),
            "comments_count": int(comment_count)
        }

        existing_data['total_posts'] = int(
            existing_data['total_posts']) + int(post_count)

        existing_data['total_comments'] = int(
            existing_data['total_comments']) + int(comment_count)

        existing_data['history'].append(new_data)

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(existing_data, file, ensure_ascii=False, indent=2)

    except Exception as e:
        lineNotify.send_notify_to_dev(f"WARNING SAVE FILE LOG: {e}.")


async def push_log_scraping(platform="", campaign="", keyword="", start_time="", end_time="", time_diff="", result_count=0):
    try:
        file_path = f"raw_logs/{platform}.txt"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "a", encoding="utf-8") as file:
            file.write(
                f"\nCampaign: {campaign}, Keyword: {keyword}, Start: {start_time}, End: {end_time}, Time Used: {time_diff}, Result: {result_count}")

    except Exception as e:
        lineNotify.send_to_scraper_problem(f"WARNING PUSH FILE LOG: {e}.")


async def push_log_cpu_used(platform="", campaign="", keyword="", part=""):
    try:
        cpu_use = psutil.cpu_percent()
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        file_name = f"{platform}.txt"
        file_path = f"raw_cpu_logs/{file_name}"

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "a", encoding="utf-8") as file:
            file.write(
                f"\nCampaign: {campaign}, Keyword: {keyword}, Datetime:{current_datetime}, Part:{part}, CPU:{cpu_use}%")

    except Exception as e:
        lineNotify.send_to_scraper_problem(f"WARNING PUSH FILE LOG CPU: {e}.")


async def push_log_csv_file(platform="", campaign="", keyword="", start_time="", end_time="", time_diff="", result=0):
    try:
        cpu_use = psutil.cpu_percent()

        file_path = f"csv_logs/{platform}.csv"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "a", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(
                [f"Campaign: {campaign}", f"Keyword: {keyword}", f"Start: {start_time}", f"End: {end_time}", f"Time Used: {time_diff}", f"CPU Used: {cpu_use}%", f"Result: {result}"])
            print(f"Write file csv {platform} success.")
    except Exception as e:
        lineNotify.send_to_scraper_problem(f"WARNING PUSH FILE LOG CPU: {e}.")
