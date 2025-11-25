from datetime import datetime, timedelta
from urllib.parse import quote

import random
import httpx
import json
import time

import envconstant.env as env
import services.keywords as keywordsService
import services.transaction as transactionService
import formatters.line_format as lineFormat
import formatters.data_format as dataFormat
import modules.file_handle as fileHandle
import modules.segmentation as segmentation
import modules.line_notify as lineNotify
import helpers.scraper as scraperHelper


async def check_process_running():
    try:
        status = await fileHandle.read_process_status(
            platform=fileHandle.process_instagram)

        if status == "1":
            return True
        else:
            return False
    except Exception as e:
        lineNotify.send_to_scraper_problem(
            message=f"Instagram\n\n error on check_process_status\n\n {e}")

        return False


async def set_process_status(status="0"):
    try:
        await fileHandle.write_process_status(
            status=status, platform=fileHandle.process_instagram)
    except Exception as e:
        lineNotify.send_to_scraper_problem(
            message=f"Instagram\n\n error on set_process_status\n\n {e}")


async def scraping_data(search_data=[]):
    campaign_lists = search_data

    for campaign in campaign_lists:
        campaign_id = campaign["campaign_id"]
        campaign_name = campaign["campaign_name"]
        organization_id = campaign["organization_id"]
        start_at = campaign["start_at"]
        end_at = campaign["end_at"]
        frequency = campaign["frequency"]
        transaction_limit = campaign["transaction_limit"]
        transaction_remaining = campaign["transaction_reamining"]

        total_result = 0

        datetime_start_campaign_scraping = datetime.now()

        try:
            transaction_limit = int(transaction_limit)
        except Exception as e:
            transaction_limit = 0

        try:
            transaction_remaining = int(transaction_remaining)
        except Exception as e:
            transaction_remaining = -1

        # TODO: condition 1 check in range date
        if not scraperHelper.is_in_range_date(start_at=start_at, end_at=end_at):
            continue

        # TODO: condition 2 check limit transaction remaining
        if not scraperHelper.is_in_transaction_limit(transaction_limit=transaction_limit, transaction_remaining=transaction_remaining):
            continue

        temp_keywords = []
        keyword_item_lists = campaign["keywords"]

        for keyword_item in keyword_item_lists:
            keyword_id = keyword_item["keyword_id"]
            keywords = keyword_item["keywords"]
            keyword_excludes = keyword_item["keyword_excludes"]
            last_craw_date = keyword_item["last_crawed_at"]

            # TODO: condition 3 check frequency
            if not scraperHelper.is_out_of_frequency(frequency_minute=frequency, last_craw_date=last_craw_date):
                continue

            await transactionService.save_last_craw_at(
                keyword_id=keyword_id,
                source_id=transactionService.source_id_instagram
            )

            number_of_result = 0
            flag_error = []

            data_result = []

            for keyword in keywords:
                temp_keywords.append(keyword)

                post_result, error = await get_post_detail(keyword=keyword, keyword_check=keywords, keyword_exclude=keyword_excludes)
                data_result.extend(post_result)

                if error != "":
                    flag_error.append(error)

            number_of_result += len(data_result)

            # todo: insert to database
            if len(data_result) > 0:
                await transactionService.updatePostsAndCommentsData(
                    data=data_result,
                    collection_name=transactionService.collection_name_instagram,
                    campaign_id=campaign_id,
                    keyword_id=keyword_id
                )

            flag_error_message = ""

            try:
                if number_of_result == 0:
                    flag_error = list(set(flag_error))
                    flag_error_message = ", ".join(flag_error)

            except Exception as e:
                lineNotify.send_to_scraper_problem(
                    message=f"Instagram\n\n error on set flag_error_message\n\n {e}")

            await transactionService.pushTransactionScrapingResult(
                keyword_id=keyword_id,
                source_id=transactionService.source_id_instagram,
                number_of_result=number_of_result,
                organization_id=organization_id,
                flag_error=flag_error_message
            )

            total_result += number_of_result

        datetime_end_campaign_scraping = datetime.now()
        keyword_str = ", ".join(temp_keywords)

        # * Notify when have keyword to scraping
        if len(temp_keywords) > 0:
            try:
                line_message = lineFormat.format_campaign_result(
                    platform="Instagram",
                    campaign_name=campaign_name,
                    keyword=keyword_str,
                    datetime_start_campaign_scraping=datetime_start_campaign_scraping,
                    datetime_end_campaign_scraping=datetime_end_campaign_scraping,
                    total_result=total_result
                )
                lineNotify.send_to_scraper_process(message=line_message)
            except Exception as e:
                lineNotify.send_to_scraper_daily_data(
                    message=f"[FINISH][ERROR]\n\nInstagram\n\nerror:\n{e}")

        try:
            datetime_diff = datetime_end_campaign_scraping - datetime_start_campaign_scraping
            diff_string = dataFormat.format_time_diff(
                diff_sec=datetime_diff.total_seconds())

            await fileHandle.push_log_csv_file(
                platform="instagram",
                campaign=campaign_name,
                keyword=keyword_str,
                start_time=datetime_start_campaign_scraping.strftime(
                    '%Y-%m-%d %H:%M'),
                end_time=datetime_end_campaign_scraping.strftime(
                    '%Y-%m-%d %H:%M'),
                time_diff=diff_string,
                result=total_result
            )
        except Exception as e:
            lineNotify.send_to_scraper_problem(
                message=f"Instagram\n\n error on push_log_csv_file\n\n {e}")

        time.sleep(2)


async def get_post_detail(keyword="", keyword_check=[], keyword_exclude=[]):

    data = []
    flag_error = ""

    current_time = datetime.now()
    if current_time.hour >= 12:
        ds_user_id = "69017308251"
        sessionid = "69017308251%3AEkb9AOIV8fZqPw%3A14%3AAYclZ8kSlO_eSex9V0N2tJU_FskS7-a7nAPYy7sI2A"
    else:
        ds_user_id = "67054051318"
        sessionid = "67054051318%3Accx7gOSfas1nuM%3A3%3AAYcEj_jR84u6pof8zXyK_RNXkJR5RunzdMxMj5bV_Q"

    try:
        user_agent_list = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36',    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_4_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1',    'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
                           'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edg/87.0.664.75',    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18363', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36']

        headers = {
            "User-Agent": user_agent_list[random.randint(0, len(user_agent_list)-1)],
            "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "*/*",
            "Cookie": f'ds_user_id={ds_user_id}; sessionid={sessionid}'
        }

        with httpx.Client(
            timeout=httpx.Timeout(20.0),
            headers=headers
        ) as session:

            query_hash = "1780c1b186e2c37de9f7da95ce41bb67"
            variables = {
                "tag_name": keyword,
                "first": 3,
                "after": None,
            }

            page = 1
            page_limit = 2

            while True:
                variables_encoded = quote(json.dumps(variables))
                url = f"https://www.instagram.com/graphql/query/?query_hash={query_hash}&variables={variables_encoded}"
                result = session.get(url)

                response = str(result.content)

                if "Please wait a few minutes before you try again" in response:
                    flag_error = 'session หมดอายุหรือถูกแบน กรุณาเปลี่ยน session ใหม่'

                    lineNotify.send_to_scraper_daily_data(message=flag_error)
                    break

                data_content = json.loads(result.content)
                posts = data_content["data"]["hashtag"]["edge_hashtag_to_media"]

                for post in posts['edges']:
                    is_excluded = False
                    is_pass = True
                    content = ""

                    try:
                        content = post['node']['edge_media_to_caption']['edges'][0]['node']['text']
                    except Exception as e:
                        continue

                    # เมื่อมีคำใดคำหนึ่งใน keyword exclude อยู่ใน content หรือ title จะไม่เก็บข้อมูล
                    if len(keyword_exclude) > 0:
                        is_excluded = any((keyword_not in content)
                                          for keyword_not in keyword_exclude)

                    # ใน content จะต้องมีทุกคำที่ต้องการ ถึงจะนำไปเก็บข้อมูล
                    if len(keyword_check) > 0:
                        is_pass = all(segmentation.compare_text_segmenting_all(
                            text=content, keyword=keyword) for keyword in keyword_check)

                    if content == "" or content == " " or content == None:
                        is_pass = False

                    if (not is_excluded) and is_pass:
                        data.append(post["node"])

                page_info = posts["page_info"]

                if not page_info["has_next_page"]:
                    break

                variables["after"] = page_info["end_cursor"]
                page += 1

                if page > page_limit:
                    break

    except Exception as e:
        lineNotify.send_to_scraper_problem(
            message=f"Instagram\n\n error on get_post_detail\n\n {e}"
        )

    return data, flag_error


async def run():
    try:
        lineNotify.send_to_scraper_daily_data(
            message=f"Instagram\n\n Run."
        )
        print("Instagram Scraper is started")

        if await check_process_running():
            print("Instagram have process running already. Exit.")
            exit()

        else:
            print("Instagram Scraper is continue running.")
            await set_process_status(
                status="1"
            )

        raw_data = await keywordsService.getActiveKeyword()
        search_data = []

        for data in raw_data:
            try:
                temp_keyword = []
                temp_keyword_exclude = []

                if isinstance(data["name"], str) and data["name"] != "":
                    temp_keyword = data["name"].split(",")

                if isinstance(data["keyword_exclude"], str) and data["keyword_exclude"] != "":
                    temp_keyword_exclude = data["keyword_exclude"].split(",")

                last_craw_date = None

                if data["id"] != None:
                    last_craw_date = await keywordsService.get_last_craw_date(keyword_id=data["id"], source_id=transactionService.source_id_instagram)

                search_data.append({
                    "campaign_id": data["campaign_id"],
                    "campaign_name": data['campaign_name'],
                    "organization_id": data["organization_id"],
                    "start_at": data["start_at"],
                    "end_at": data["end_at"],
                    "frequency": data["frequency"],
                    "transaction_limit": data["transaction_limit"],
                    "transaction_reamining": data["transaction_reamining"],
                    "keyword_id": data["id"],
                    "keyword": temp_keyword,
                    "keyword_exclude": temp_keyword_exclude,
                    "last_crawed_at": last_craw_date,
                })
            except Exception as e:
                err_message = f"WARNING instagram:\n\n in loop format raw data \n\n {e}"
                lineNotify.send_notify_to_dev(message=err_message)

        # * [NOTIFY]: Notify when have keyword to scraping
        lineNotify.send_to_scraper_daily_data(
            message=f"Instagram\n\n มีการสั่งให้ทำงาน จำนวน:{len(search_data)} keyword."
        )

        if len(search_data) > 0:
            try:
                formatted_search_data = dataFormat.format_keyword_group_by_campaign(
                    raw_data=search_data
                )

                await scraping_data(search_data=formatted_search_data)
            except Exception as e:
                err_message = f"Instagram\n\n scraping not working \n\n {e}"
                lineNotify.send_notify_to_dev(message=err_message)

        else:
            message = f"Instagram\n\n ไม่พบ Keywords ที่ต้องการกวาดข้อมูล."
            lineNotify.send_notify_scraping_result(message=message)

        await set_process_status(
            status="0"
        )
    except Exception as e:
        lineNotify.send_to_scraper_problem(
            message=f"Instagram\n\n error on run\n\n {e}")

        await set_process_status(
            status="0"
        )
