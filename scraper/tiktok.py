from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver

from TikTokApi import TikTokApi
from datetime import datetime

from modules import telegram_notify

import envconstant.env as env
import driver.main as driverInstant
import formatters.tiktok_format as tiktokFormatter
import formatters.line_format as lineFormat
import formatters.data_format as dataFormat
import modules.file_handle as fileHandle
import modules.segmentation as segmentation
import services.keywords as keywordsService
import services.transaction as transactionService
import helpers.scraper as scraperHelper
import helpers.error_handle as errorHandle
import xpath.tikTok as xpathTikTok

import time


async def check_process_running():
    try:
        status = await fileHandle.read_process_status(
            platform=fileHandle.process_tiktok)

        if status == "1":
            return True
        else:
            return False
    except Exception as e:
        message_err = f"Tiktok\n\n error on check_process_status\n\n {e}"
        telegram_notify.send_to_private(message=message_err)

        return False


async def set_process_status(status="0"):
    try:
        await fileHandle.write_process_status(
            status=status, platform=fileHandle.process_tiktok)
    except Exception as e:
        message_err = f"Tiktok\n\n error on set_process_status\n\n {e}"
        telegram_notify.send_to_private(message=message_err)


def get_link_video_by_keyword(driver, wait, index=0, keyword=""):
    if keyword == "":
        return []

    index = int(index) + 1

    if index > 40:
        return []

    try:
        links = []
        timestamp = int(datetime.now().timestamp())

        driver.get(
            f"https://www.tiktok.com/search?q={keyword}&t={timestamp}")
        wait.until(EC.presence_of_element_located(
            (By.XPATH, xpathTikTok.video_link())))

        links_video = driver.find_elements(
            "xpath", xpathTikTok.video_link())

        for lv in links_video:
            links.append(lv.get_attribute("href"))

        return links
    except Exception as e:
        result = get_link_video_by_keyword(driver, wait, index, keyword)

        return result


async def get_videos_and_comments(urls=[], keyword__id="", keyword_check=[], keyword_exclude=[], ms_token="", count_video=30, count_comment=30):
    data_result = []

    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3)

        for url in urls:
            try:
                video = api.video(
                    url=url
                )

                video_info = await video.info()
                video_formatted = tiktokFormatter.format_data_video(
                    video_info)

                # TODO: check content less than 1 day [check in format_data_video]
                if video_formatted == None:
                    continue

                is_excluded = False
                is_pass = True

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
                    data_result.append(tiktokFormatter.format_data_for_mysql(
                        keyword_id=keyword__id,
                        id_str=video_formatted.get("id_str") or None,
                        ref_id="",
                        full_text=video_formatted.get("full_text") or None,
                        source=video_formatted.get("source") or None,
                        post_date=video_formatted.get("post_date") or None,
                        account_name=video_formatted.get(
                            "account_name") or None,
                        content_images=video_formatted.get(
                            "content_images") or [],
                        profile_image=video_formatted.get(
                            "profile_image") or None,
                        message_type="Post",
                        bookmark_count=video_formatted.get(
                            "bookmark_count") or 0,
                        comment_count=video_formatted.get(
                            "comment_count") or 0,
                        repost_count=video_formatted.get("repost_count") or 0,
                        shares=video_formatted.get("shares") or 0,
                        like=video_formatted.get("like") or 0,
                        view=video_formatted.get("view") or 0
                    ))

                    async for comment in video.comments(count=count_comment):
                        try:
                            comment_formatted = tiktokFormatter.format_data_video_comment(
                                comment.as_dict)

                            data_result.append(
                                tiktokFormatter.format_data_for_mysql(
                                    keyword_id=keyword__id,
                                    id_str=comment_formatted.get(
                                        "id_str") or None,
                                    ref_id=video_formatted.get(
                                        "id_str") or "",
                                    full_text=comment_formatted.get(
                                        "full_text") or None,
                                    source=comment_formatted.get(
                                        "source") or None,
                                    post_date=comment_formatted.get(
                                        "post_date") or None,
                                    account_name=comment_formatted.get(
                                        "account_name") or None,
                                    content_images=comment_formatted.get(
                                        "content_images") or [],
                                    profile_image=comment_formatted.get(
                                        "profile_image") or None,
                                    message_type="Comment",
                                    bookmark_count=0,
                                    comment_count=comment_formatted.get(
                                        "reply_comment_count") or 0,
                                    repost_count=0,
                                    shares=0,
                                    like=comment_formatted.get(
                                        "like") or 0,
                                    view=comment_formatted.get("view") or 0
                                ))
                        except Exception as e:
                            message_err = f"Tiktok WARNING in async for comment in video:\n {e}"

                            telegram_notify.send_to_tiktok_private(
                                message=message_err)
            except Exception as e:
                message_err = f"Tiktok WARNING in call video:\n {e}"
                telegram_notify.send_to_tiktok_private(
                    message=message_err)

    return data_result


async def scraping_data(search_data=[], count_video=30, count_comment=30):
    def create_my_driver(index=0):
        try:
            time.sleep(1)

            if index > 2:
                return None

            chrome_options = webdriver.ChromeOptions()
            # chrome_options.add_argument("--incognito")
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            # chrome_options.add_argument("--disable-dev-shm-usage")
            # chrome_options.add_argument("--disable-application-cache")

            my_driver = webdriver.Chrome(options=chrome_options)

            my_dict = {}
            my_dict["driver"] = my_driver
            my_dict["index"] = index

            return my_dict
        except Exception as e:
            return create_my_driver(index=index+1)

    campaign_lists = search_data

    total_count_result = 0

    try:
        result_create_driver = create_my_driver()

        if result_create_driver == None:
            raise Exception("Can't create web driver.")

        tiktok_driver = result_create_driver['driver']
        tiktok_wait = WebDriverWait(tiktok_driver, 10)

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
            total_insert = 0
            total_update = 0

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
                    source_id=transactionService.source_id_tiktok
                )

                number_of_result = 0
                flag_error = []
                ms_token = env.TIKTOK_MS_TOKEN

                for keyword in keywords:
                    temp_keywords.append(f"{keyword}({keyword_id})")

                    data_result = []
                    links_from_keyword = []

                    try:
                        links_from_keyword = get_link_video_by_keyword(
                            driver=tiktok_driver, wait=tiktok_wait, keyword=keyword)

                    except Exception as e:
                        telegram_notify.send_to_private(
                            message=f"Tiktok error get_link_video_by_keyword\n\n {e}")
                        continue

                    try:
                        data_result = await get_videos_and_comments(
                            urls=links_from_keyword,
                            keyword__id=keyword_id,
                            keyword_check=keywords,
                            keyword_exclude=keyword_excludes,
                            count_video=count_video,
                            count_comment=count_comment,
                            ms_token=ms_token
                        )

                        number_of_result += len(data_result)

                        # todo: insert to database
                        if len(data_result) > 0:
                            insert_len, update_len = await transactionService.insert_post_and_comments_data_to_mysql(new_data=data_result)
                            total_insert += insert_len
                            total_update += update_len

                            # * insert to second database
                            await transactionService.insert_post_and_comments_data_to_mysql(new_data=data_result, isSecondDB=True)

                    except Exception as e:
                        # todo: =============> START: handle error <============
                        try:
                            result_message = errorHandle.handle(e)

                            if result_message["is_error"]:
                                if "ส่งถึง Developer" in result_message['message']:
                                    pass

                                else:
                                    flag_error.append(
                                        f"{result_message['message']}")

                        except Exception as ee:
                            pass
                        # todo: =============> END: handle error <============

                flag_error_message = ""

                try:
                    if number_of_result == 0:
                        flag_error = list(set(flag_error))
                        flag_error_message = ", ".join(flag_error)

                except Exception as e:
                    pass

                await transactionService.pushTransactionScrapingResult(
                    keyword_id=keyword_id,
                    source_id=transactionService.source_id_tiktok,
                    number_of_result=number_of_result,
                    organization_id=organization_id,
                    flag_error=flag_error_message
                )

                total_result += number_of_result

            datetime_end_campaign_scraping = datetime.now()
            keyword_str = ", ".join(temp_keywords)

            if len(temp_keywords) > 0:
                try:
                    line_message = lineFormat.format_campaign_result(
                        platform="Tiktok",
                        campaign_name=campaign_name,
                        campaign_id=campaign_id,
                        keyword=keyword_str,
                        datetime_start_campaign_scraping=datetime_start_campaign_scraping,
                        datetime_end_campaign_scraping=datetime_end_campaign_scraping,
                        total_result=total_result,
                        total_insert=total_insert,
                        total_update=total_update,
                    )
                    telegram_notify.send_to_tiktok_work_process(
                        message=line_message)
                except Exception as e:
                    telegram_notify.send_to_tiktok_private(
                        message=f"[FINISH][ERROR]\n\nTiktok\n\nerror:\n{e}")

            total_count_result += total_result

            time.sleep(2)

        try:
            tiktok_driver.close()
            tiktok_driver.quit()
        except Exception as e:
            pass

    except Exception as e:
        telegram_notify.send_to_tiktok_private(
            message=f"Error in main function tiktok.\n{e}")

    return total_count_result


async def run():
    try:
        print("Tiktok scraping call to start.")
        telegram_notify.send_to_tiktok_work_process(
            "Tiktok scraping call to start.")

        while True:
            try:
                vcount = 30  # driverInstant.get_video_count_from_argv()
                ccount = 30  # driverInstant.get_video_comment_count_from_argv()

                raw_data = await keywordsService.getActiveKeyword(platform=keywordsService.platform_tiktok)
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

                try:
                    telegram_notify.send_to_tiktok_private(
                        message=f"TIKTOK START\n\n {len(search_data)} keywords found.")
                except Exception as e:
                    telegram_notify.send_to_pantip_private(
                        message=f"___________TIKTOK ERROR\n\n {e}")
                    pass

                if len(search_data) > 0:
                    formatted_search_data = dataFormat.format_keyword_group_by_campaign(
                        raw_data=search_data
                    )

                    if len(formatted_search_data) > 0:
                        try:
                            await scraping_data(search_data=formatted_search_data, count_video=vcount, count_comment=ccount)

                            del formatted_search_data, raw_data, search_data

                        except Exception as e:
                            telegram_notify.send_to_tiktok_private(
                                message=f"Tiktok\n\n scraping not working \n\n {e}")
                else:
                    telegram_notify.send_to_tiktok_work_process(
                        message=f"Tiktok\n\n ไม่พบ Keywords ที่ต้องการกวาดข้อมูล.")

            except Exception as e:
                telegram_notify.send_to_tiktok_private(
                    message=f"error:end process\n\n {e}")

            time.sleep(60 * 10)

    except Exception as e:
        telegram_notify.send_to_tiktok_private(
            message=f"Error while loop\n\n{e}")
