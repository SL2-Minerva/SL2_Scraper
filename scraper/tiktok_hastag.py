from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from TikTokApi import TikTokApi
from datetime import datetime

import envconstant.env as env
import driver.main as driverInstant
import formatters.tiktok_format as tiktokFormatter
import formatters.line_format as lineFormat
import formatters.data_format as dataFormat
import modules.file_handle as fileHandle
import modules.line_notify as lineNotify
import modules.segmentation as segmentation
import services.keywords as keywordsService
import services.transaction as transactionService
import services.tiktok as tiktokService
import helpers.scraper as scraperHelper
import helpers.error_handle as errorHandle


async def run():
    print("Tiktok Scraper is running...")

    vcount = driverInstant.get_video_count_from_argv()
    ccount = driverInstant.get_video_comment_count_from_argv()

    print(f"video count: {vcount}, comment count: {ccount}")

    raw_data = await keywordsService.getActiveKeyword()
    search_data = []

    for data in raw_data:
        tempKeyword = []
        tempKeywordExclude = []

        if isinstance(data["name"], str) and data["name"] != "":
            tempKeyword = data["name"].split(",")

        if isinstance(data["keyword_exclude"], str) and data["keyword_exclude"] != "":
            tempKeywordExclude = data["keyword_exclude"].split(",")

        last_craw_date = None

        if data["id"] != None:
            last_craw_date = await keywordsService.get_last_craw_date(keyword_id=data["id"], source_id=transactionService.source_id_tiktok)

        search_data.append({
            "keyword_id": data["id"],
            "campaign_id": data["campaign_id"],
            "campaign_name": data['campaign_name'],
            "organization_id": data["organization_id"],
            "start_at": data["start_at"],
            "end_at": data["end_at"],
            "frequency": data["frequency"],
            "transaction_limit": data["transaction_limit"],
            "transaction_reamining": data["transaction_reamining"],
            "last_crawed_at": last_craw_date,
            "keyword": tempKeyword,
            "keyword_exclude": tempKeywordExclude,
        })

    if len(search_data) > 0:
        try:
            await scraping_data(search_data=search_data, count_video=vcount, count_comment=ccount)
        except Exception as e:
            message_err = f"Tiktok:\n\n scraping not working \n\n {e}"
            lineNotify.send_notify_to_dev(message=message_err)
    else:
        message = f"Tiktok\n\n ไม่พบ Keywords ที่ต้องการกวาดข้อมูล."
        lineNotify.send_notify_scraping_result(message=message)


async def scraping_data(search_data=[], count_video=30, count_comment=30):
    transaction_success = 0
    round_of_scraping = 0
    total_result = 0

    datetime_start_scraping = datetime.now()
    data_error = []

    try:
        message = f'[RUN]\n\n Tiktok\n\n At: {datetime_start_scraping.strftime("%Y-%m-%d %H:%M:%S")}\n\nSearch data count: {len(search_data)}'
        lineNotify.send_to_scraper_process(message=message)
    except Exception as e:
        pass

    try:
        for search in search_data:
            round_of_scraping += 1

            try:
                keyword_id = search["keyword_id"]
                campaign_id = search["campaign_id"]
                campaign_name = search["campaign_name"]
                organization_id = search["organization_id"]
                start_at = search["start_at"]
                end_at = search["end_at"]
                frequency = search["frequency"]
                last_craw_date = search["last_crawed_at"]
                transaction_limit = search["transaction_limit"]
                transaction_remaining = search["transaction_reamining"]

                try:
                    transaction_limit = int(transaction_limit)
                except Exception as e:
                    transaction_limit = 0

                    err_message = f"WARNING [tiktok API]:\n int(transaction_limit) \n\n {e}"
                    lineNotify.send_notify_to_dev(message=err_message)

                try:
                    transaction_remaining = int(transaction_remaining)
                except Exception as e:
                    transaction_remaining = -1

                    err_message = f"WARNING [tiktok API]:\n int(transaction_remaining) \n\n {e}"
                    lineNotify.send_notify_to_dev(message=err_message)

                # TODO: condition 1 check in range date
                if not scraperHelper.is_in_range_date(start_at=start_at, end_at=end_at):
                    # try:
                    #     text_message = f"Tiktok\n\nCampaign: {campaign_name}\n\nไม่อยู่ในช่วงวันที่กำหนด\n\nStart: {start_at}\nEnd: {end_at}"
                    #     lineNotify.send_to_scraper_daily_data(
                    #         message=text_message)
                    # except Exception as e:
                    #     text_message = f"Tiktok\n\nCampaign: {campaign_name}\n\nไม่อยู่ในช่วงวันที่กำหนด\n\nerror\n {e}"
                    #     lineNotify.send_to_scraper_problem(
                    #         message=text_message)

                    continue

                # TODO: condition 2 check limit transaction remaining
                if not scraperHelper.is_in_transaction_limit(transaction_limit=transaction_limit, transaction_remaining=transaction_remaining):
                    # try:
                    #     text_message = f"Tiktok\n\nCampaign: {campaign_name}\n\nLimit transaction ไม่เข้าเงือนไข\n\nTransaction limit: {transaction_limit}\nTransaction remaining: {transaction_remaining}"
                    #     lineNotify.send_to_scraper_daily_data(
                    #         message=text_message)
                    # except Exception as e:
                    #     text_message = f"Tiktok\n\nCampaign: {campaign_name}\n\nLimit transaction ไม่เข้าเงือนไข\n\nerror\n {e}"
                    #     lineNotify.send_to_scraper_problem(
                    #         message=text_message)

                    continue

                # TODO: condition 3 check frequency
                if not scraperHelper.is_out_of_frequency(frequency_minute=frequency, last_craw_date=last_craw_date):
                    # try:
                    #     text_message = f"Tiktok\n\nCampaign: {campaign_name}\n\nไม่ถึงรอบที่ต้องกวาด\n\nfrequency: {frequency}\nLast craw: {last_craw_date}"
                    #     lineNotify.send_to_scraper_daily_data(
                    #         message=text_message)
                    # except Exception as e:
                    #     text_message = f"Tiktok\n\nCampaign: {campaign_name}\n\nไม่ถึงรอบที่ต้องกวาด\n\nerror\n {e}"
                    #     lineNotify.send_to_scraper_problem(
                    #         message=text_message)

                    continue

                keywords = search["keyword"]
                keyword_exclude = search["keyword_exclude"]

                number_of_result = 0
                flag_error = []
                keyword_check = keywords

                ms_token = env.TIKTOK_MS_TOKEN

                for keyword in keywords:
                    data_result = []

                    try:
                        data_result = await get_videos_and_comments(
                            keyword=keyword,
                            keyword_check=keyword_check,
                            keyword_exclude=keyword_exclude,
                            count_video=count_video,
                            count_comment=count_comment,
                            ms_token=ms_token
                        )

                        number_of_result += len(data_result)

                        # todo: insert to database
                        if len(data_result) > 0:
                            await tiktokService.updatePostsAndCommentsData(data=data_result, campaign_id=campaign_id, keyword_id=keyword_id)

                    except Exception as e:
                        # todo: =============> START: handle error <============
                        try:
                            result_message = errorHandle.handle(e)

                            if result_message["is_error"]:
                                if "ส่งถึง Developer" in result_message['message']:

                                    msg = f"Tiktok\n\nerror:\n{keyword}\n\n{result_message['message']}"
                                    lineNotify.send_notify_to_dev(
                                        message=msg)

                                    flag_error.append(
                                        "เว็บไซต์ปลายทางไม่ตอบสนองในขณะนั้น อาจเกิดจากมีการส่ง request จากผู้ใช้งานพร้อมกันเป็นจำนวนมาก")
                                else:
                                    data_error = dataFormat.set_keyword_error(
                                        data=data_error, type_error=result_message['message'], keyword=keyword)
                                    flag_error.append(
                                        result_message['message'])

                        except Exception as ee:
                            message_err = f"Tiktok\n\n error on errorHandle\n\n {ee}"
                            lineNotify.send_to_scraper_problem(
                                message=message_err)
                        # todo: =============> END: handle error <============

                flag_error_message = ""

                try:
                    if number_of_result == 0:
                        flag_error = list(set(flag_error))
                        flag_error_message = ", ".join(flag_error)
                except Exception as e:
                    message_err = f"Tiktok\n\n error on set flag_error_message\n\n {e}"
                    lineNotify.send_to_scraper_problem(message=message_err)

                await transactionService.pushTransactionScrapingResult(
                    keyword_id=keyword_id,
                    source_id=transactionService.source_id_tiktok,
                    number_of_result=number_of_result,
                    organization_id=organization_id,
                    flag_error=flag_error_message
                )

                transaction_success += 1
                total_result += number_of_result

            except Exception as e:
                message_err = f"Tiktok\n\n in for search in search_data:\n\n {e}"
                lineNotify.send_notify_to_dev(message=message_err)

    except Exception as e:
        message_err = f"Tiktok\n\n In Main [TikTokApi]:\n {e}"
        lineNotify.send_notify_to_dev(message=message_err)

    if len(data_error) > 0:
        try:
            message_err = "Tiktok Warning.\n\n"
            i = 0

            for err in data_error:
                i += 1
                message_err += f'{i}. Error:{err["type_error"]}\nKeyword: {", ".join(err["keywords"])}\n\n'

            lineNotify.send_to_scraper_problem(message=message_err)
        except Exception as e:
            message_err = f"Tiktok\n\n error in data_error \n\n {e}"
            lineNotify.send_to_scraper_problem(message=message_err)

    try:
        datetime_end_scraping = datetime.now()
        datetime_diff = datetime_end_scraping - datetime_start_scraping
        diff_string = dataFormat.format_time_diff(
            diff_sec=datetime_diff.total_seconds())

        message = f'[FINISH]\n\nTiktok\n\nAt: {datetime_end_scraping.strftime("%Y-%m-%d %H:%M")}\n\nTime of scraping:{diff_string}\n\nRound of scraping:{round_of_scraping}\nSuccess:{transaction_success}\nResult:{total_result}\n\nData error: {len(data_error)}'
        lineNotify.send_to_scraper_process(message=message)
    except Exception as e:
        message2 = f"[FINISH][ERROR]\n\nTiktok\n\nerror:\n{e}"
        lineNotify.send_to_scraper_process(message=message2)


async def get_videos_and_comments(keyword="", keyword_check=[], keyword_exclude=[], ms_token="", count_video=30, count_comment=30):
    data_result = []

    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3)

        try:
            tag = api.hashtag(name=keyword)
        except Exception as e:
            tag = api.hashtag(name=keyword.split()[0])

        async for video in tag.videos(count=count_video):
            try:
                video_formatted = tiktokFormatter.format_data_video(
                    video.as_dict)

                is_pass = False
                is_excluded = False

                content = video_formatted["full_text"]

                # เมื่อมีคำใดคำหนึ่งใน keyword exclude อยู่ใน content หรือ title จะไม่เก็บข้อมูล
                if len(keyword_exclude) > 0:
                    is_excluded = any((keyword_not in content)
                                      for keyword_not in keyword_exclude)

                if len(keyword_check) > 0:
                    is_pass = all(segmentation.compare_text_segmenting_all(
                        text=content, keyword=keyword) for keyword in keyword_check)

                if content == "" or content == " " or content == None:
                    is_pass = False

                if (not is_excluded) and is_pass:
                    data_result.append(video_formatted)

                    async for comment in video.comments(count=count_comment):
                        try:
                            comment_formatted = tiktokFormatter.format_data_video_comment(
                                comment.as_dict)

                            comment_is_pass = False
                            comment_is_excluded = False

                            full_text = comment_formatted["full_text"]

                            # เมื่อมีคำใดคำหนึ่งใน keyword exclude อยู่ใน content หรือ title จะไม่เก็บข้อมูล
                            if len(keyword_exclude) > 0:
                                comment_is_excluded = any(
                                    (keyword_not in full_text) for keyword_not in keyword_exclude)

                            # ใน full_text จะต้องมีทุกคำที่ต้องการ ถึงจะนำไปเก็บข้อมูล
                            if len(keyword_check) > 0:
                                comment_is_pass = all((segmentation.compare_text_segmenting_all(text=full_text, keyword=keyword))
                                                      for keyword in keyword_check)

                            if full_text == "" or full_text == " " or full_text == None:
                                comment_is_pass = False

                            if (not comment_is_excluded) and comment_is_pass:
                                data_result.append(
                                    comment_formatted)
                        except Exception as e:
                            message_err = f"WARNING in async for comment in video:\n {e}"

                            lineNotify.send_notify_to_dev(
                                message=message_err)
            except Exception as e:
                message_err = f"WARNING in async for video in tag.videos:\n {e}"

                if "empty response" not in message_err:
                    lineNotify.send_notify_to_dev(message=message_err)

    return data_result
