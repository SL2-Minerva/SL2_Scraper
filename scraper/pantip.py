
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from datetime import datetime, timedelta

# import random
# import json
import time
import driver.main as driverInstant
import xpath.pantip as xpathPantip
import services.keywords as keywordsService
import services.transaction as transactionService
import modules.file_handle as fileHandle
import modules.segmentation as segmentation
import modules.line_notify as lineNotify
import formatters.data_format as dataFormat
import formatters.line_format as lineFormat
import helpers.scraper as scraperHelper
import helpers.error_handle as errorHandle


async def check_process_running():
    try:
        status = await fileHandle.read_process_status(
            platform=fileHandle.process_pantip)

        if status == "1":
            return True
        else:
            return False
    except Exception as e:
        message_err = f"Pantip\n\n error on check_process_status\n\n {e}"
        lineNotify.send_to_scraper_problem(message=message_err)

        return False


async def set_process_status(status="0"):
    try:
        await fileHandle.write_process_status(
            status=status, platform=fileHandle.process_pantip)
    except Exception as e:
        message_err = f"Pantip\n\n error on set_process_status\n\n {e}"
        lineNotify.send_to_scraper_problem(message=message_err)


async def scraping_data(search_data=[], paging=1):
    def create_my_driver(index=0):
        try:
            time.sleep(1)

            if index > 800:
                return None

            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--incognito")
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-application-cache")

            my_driver = webdriver.Chrome(options=chrome_options)

            my_dict = {}
            my_dict["driver"] = my_driver
            my_dict["index"] = index

            return my_dict
        except Exception as e:
            return create_my_driver(index=index+1)

    result_create_driver = create_my_driver()

    pantip_driver = result_create_driver['driver']
    patip_wait = WebDriverWait(pantip_driver, 15)

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
            # lineNotify.send_to_scraper_process(
            #     message=f"Pantip\n\n Campaign: {campaign_name} ไม่เข้าเงือนไขช่วงเวลา.\n\n{start_at} - {end_at}")
            continue

        # TODO: condition 2 check limit transaction remaining
        if not scraperHelper.is_in_transaction_limit(transaction_limit=transaction_limit, transaction_remaining=transaction_remaining):
            # lineNotify.send_to_scraper_process(
            #     message=f"Pantip\n\n Campaign: {campaign_name} ไม่เข้าเงือนไข limit\n\n transaction_limit:{transaction_limit}\n transaction_remaining:{transaction_remaining}")
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

                # lineNotify.send_to_scraper_process(
                #     message=f"Pantip\n\n Campaign: {campaign_name} Keyword:{keywords}\nไม่เข้าเงือนไข frequency\n\n frequency:{frequency}\n last_craw_date:{last_craw_date}")
                continue

            await transactionService.save_last_craw_at(
                keyword_id=keyword_id,
                source_id=transactionService.source_id_pantip
            )

            number_of_result = 0
            flag_error = []

            for keyword in keywords:
                temp_keywords.append(f"{keyword}({keyword_id})")

                url = f"https://pantip.com/search?q={keyword}&timebias=true"

                topic_url = []
                data_result = []

                try:
                    pantip_driver.get(url)
                    patip_wait.until(EC.presence_of_element_located(
                        (By.XPATH, xpathPantip.post_link())))

                    # ********** [START] Get link of post **********

                    for i in range(0, paging):
                        pantip_driver.execute_script(
                            "window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(2)

                    post_link = pantip_driver.find_elements(
                        "xpath", xpathPantip.post_link())

                    for link in post_link:
                        topic_url.append(link.get_attribute("href"))

                    # ********** [END] Get link of post **********

                    for temp_url in topic_url:
                        try:
                            post_result = await get_post_detail_and_comments(topic_url=temp_url, driver=pantip_driver, keyword_check=keywords, keyword_exclude=keyword_excludes)
                            data_result.extend(post_result)

                        except Exception as e:

                            # todo: =============> START: handle error <============
                            try:
                                result_message = errorHandle.handle(e)

                                if result_message["is_error"]:
                                    if "ส่งถึง Developer" in result_message['message']:
                                        lineNotify.send_notify_to_dev(
                                            message=f"Pantip\n\nerror on [for url in topic_url]:\n{keyword}\n\n{result_message['message']}")

                                        flag_error.append(
                                            "ไม่พบ Post ที่ตรงกัน หรือ เว็บไซต์ปลายทางไม่ตอบสนองในขณะนั้น")
                                    else:
                                        flag_error.append(
                                            f"{result_message['message']}")

                            except Exception as ee:
                                lineNotify.send_to_scraper_problem(
                                    message=f"Pantip\n\n error on errorHandle at [error on for url in topic_url]\n\n {ee}")
                            # todo: =============> END: handle error <============

                    number_of_result += len(data_result)

                    # todo: insert to database
                    if len(data_result) > 0:
                        await transactionService.updatePostsAndCommentsData(
                            data=data_result,
                            collection_name=transactionService.collection_name_pantip,
                            campaign_id=campaign_id,
                            keyword_id=keyword_id
                        )

                except Exception as e:
                    # todo: =============> START: handle error <============
                    try:
                        result_message = errorHandle.handle(e)

                        if result_message["is_error"]:
                            if "ส่งถึง Developer" in result_message['message']:
                                msg = f"Pantip\n\nPost not found with keyword:\n{keyword}\n\n{result_message['message']}"
                                lineNotify.send_notify_to_dev(message=msg)

                                flag_error.append(
                                    "ไม่พบ Post ที่ตรงกัน หรือ เว็บไซต์ปลายทางไม่ตอบสนองในขณะนั้น")
                            else:
                                flag_error.append(
                                    f"{result_message['message']}")

                    except Exception as ee:
                        message_err = f"Pantip\n\n error on errorHandle\n\n {ee}"
                        lineNotify.send_to_scraper_problem(message=message_err)
                    # todo: =============> END: handle error <============

                time.sleep(1)

            flag_error_message = ""

            try:
                if number_of_result == 0:
                    flag_error = list(set(flag_error))
                    flag_error_message = ", ".join(flag_error)

            except Exception as e:
                lineNotify.send_to_scraper_problem(
                    message=f"Pantip\n\n error on set flag_error_message\n\n {e}")

            await transactionService.pushTransactionScrapingResult(
                keyword_id=keyword_id,
                source_id=transactionService.source_id_pantip,
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
                    platform="Pantip",
                    campaign_name=campaign_name,
                    campaign_id=campaign_id,
                    keyword=keyword_str,
                    datetime_start_campaign_scraping=datetime_start_campaign_scraping,
                    datetime_end_campaign_scraping=datetime_end_campaign_scraping,
                    total_result=total_result
                )
                lineNotify.send_to_scraper_process(message=line_message)
            except Exception as e:
                lineNotify.send_to_scraper_daily_data(
                    message=f"[FINISH][ERROR]\n\nPantip\n\nerror:\n{e}")

        try:
            datetime_diff = datetime_end_campaign_scraping - datetime_start_campaign_scraping
            diff_string = dataFormat.format_time_diff(
                diff_sec=datetime_diff.total_seconds())

            await fileHandle.push_log_csv_file(
                platform="pantip",
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
                message=f"Pantip\n\n error on push_log_csv_file\n\n {e}")

        time.sleep(2)

    try:
        # pantip_driver.close()
        pantip_driver.quit()
    except Exception as e:
        pass


async def get_post_detail_and_comments(topic_url="", driver=None, keyword_check=[], keyword_exclude=[], activity_count=0):
    print(f"{topic_url}")

    driver.get(topic_url)

    wait = WebDriverWait(driver, 30)

    data = []

    is_excluded = False
    is_pass = True

    try:
        time.sleep(4)
        wait.until(EC.presence_of_element_located(
            (By.XPATH, xpathPantip.post_title())))

        title = driver.find_element(
            "xpath", xpathPantip.post_title()).get_attribute("textContent").replace("\t", "").replace("\n", "")
        content = driver.find_element(
            "xpath", xpathPantip.post_content()).get_attribute("textContent").replace("\t", "").replace("\n", "")
        content_imgs_ele = driver.find_elements(
            "xpath", xpathPantip.post_images())
        like = driver.find_element(
            "xpath", xpathPantip.post_like()).get_attribute("textContent")

        # เมื่อมีคำใดคำหนึ่งใน keyword exclude อยู่ใน content หรือ title จะไม่เก็บข้อมูล
        if len(keyword_exclude) > 0:
            is_excluded = any((keyword_not in content or keyword_not in title)
                              for keyword_not in keyword_exclude)

        # ใน content จะต้องมีทุกคำที่ต้องการ ถึงจะนำไปเก็บข้อมูล
        if len(keyword_check) > 0:
            is_pass = all((segmentation.compare_text_segmenting_all(text=content, keyword=keyword) or segmentation.compare_text_segmenting_all(text=title, keyword=keyword))
                          for keyword in keyword_check)

        if content == "" or content == None:
            is_pass = False

        if (not is_excluded) and is_pass:
            # handle case user profile is icon/image
            try:
                account_name = driver.find_element(
                    "xpath", xpathPantip.post_account_name()).get_attribute("textContent")
            except Exception as e:
                account_name = ""

            datetime = driver.find_element(
                "xpath", xpathPantip.post_datetime()).get_attribute("data-utime")

            content_images = []

            try:
                for img in content_imgs_ele:
                    content_images.append(img.get_attribute("src"))
            except Exception as e:
                pass

            data.append({
                "title":  f"{title}",
                "full_text":  f"{content}",
                "content_images": content_images,
                "url":  f"{topic_url}",
                "message_type": "post",
                "author":  f"{account_name}",
                "post_date":  f"{datetime}",
                "like": like,
            })
    except Exception as e:
        lineNotify.send_notify_to_dev(
            message=f"Pantip\n\n error at find post: \n {topic_url} \n\n {e}")

    if (not is_excluded) and is_pass:
        try:
            wait.until(EC.presence_of_element_located(
                (By.XPATH, xpathPantip.comment_box_content())))

            comments = driver.find_elements(
                By.XPATH, xpathPantip.comment_box_content())

            index = 0

            for comment in comments:
                index += 1
                comment_is_pass = True
                comment_is_excluded = False

                try:
                    # handle case user profile is icon/image
                    try:
                        comment_account_name = comment.find_element(
                            "xpath",
                            xpathPantip.comment_account_name(
                                only_xpath=False,
                                length=index
                            )
                        ).get_attribute("textContent").replace("\t", "").replace("\n", "")
                    except Exception as e:
                        comment_account_name = ""

                    try:
                        full_text = comment.find_element(
                            "xpath",
                            xpathPantip.comment_content(
                                only_xpath=False,
                                length=index
                            )
                        ).get_attribute("textContent").replace("\t", "").replace("\n", "")
                    except Exception as e:
                        full_text = "null"

                    # เมื่อมีคำใดคำหนึ่งใน keyword exclude อยู่ใน content หรือ title จะไม่เก็บข้อมูล
                    if len(keyword_exclude) > 0:
                        comment_is_excluded = any(
                            (keyword_not in full_text) for keyword_not in keyword_exclude)

                    # ใน full_text จะต้องมีทุกคำที่ต้องการ ถึงจะนำไปเก็บข้อมูล
                    if len(keyword_check) > 0:
                        comment_is_pass = all((segmentation.compare_text_segmenting_all(text=full_text, keyword=keyword))
                                              for keyword in keyword_check)

                    if full_text == "" or full_text == None:
                        comment_is_pass = False

                    if (not comment_is_excluded) and comment_is_pass:
                        try:
                            comments_datetime = comment.find_element(
                                "xpath",
                                xpathPantip.comment_datetime(
                                    only_xpath=False,
                                    length=index
                                )
                            ).get_attribute("data-utime").replace("\t", "").replace("\n", "")
                        except Exception as e:
                            comments_datetime = "null"

                        try:
                            comment_like = comment.find_element(
                                "xpath",
                                xpathPantip.comment_like(
                                    only_xpath=False,
                                    length=index
                                )
                            ).get_attribute("textContent").replace("\t", "").replace("\n", "")
                        except Exception as e:
                            comment_like = "0"

                        content_images = []

                        try:
                            images_ele = comment.find_elements(
                                "xpath",
                                xpathPantip.comment_images(
                                    only_xpath=False,
                                    length=index
                                )
                            )
                        except Exception as e:
                            images_ele = []

                        try:
                            for img in images_ele:
                                content_images.append(img.get_attribute("src"))
                        except Exception as e:
                            pass

                        data.append({
                            "full_text":  f"{full_text}",
                            "message_type": "comment",
                            "url": f"{topic_url}",
                            "author": f"{comment_account_name}",
                            "post_date": f"{comments_datetime}",
                            "like": comment_like,
                            "content_images": content_images,
                        })
                except Exception as e:
                    message = f"Pantip\n\n error at comments_content: {topic_url}\n\n {e}"
                    lineNotify.send_notify_to_dev(message)

        except Exception as e:
            pass

    print(f"activity count: {len(data)}")

    return data


async def run():
    try:
        print("Pantip Scraper is started.")

        if await check_process_running():
            print("Pantip have process running already. Exit.")

            lineNotify.send_to_scraper_daily_data(
                message=f"Pantip\n\n มีกระบวนการกวาดข้อมูลทำงานอยู่แล้ว."
            )
            exit()
        else:
            print("Pantip Scraper is continue running.")
            await set_process_status(
                status="1"
            )

        paging = driverInstant.get_paging_from_argv()

        raw_data = await keywordsService.getActiveKeyword()
        search_data = []

        for data in raw_data:
            try:
                tempKeyword = []
                tempKeywordExclude = []

                if isinstance(data["name"], str) and data["name"] != "":
                    tempKeyword = data["name"].split(",")

                if isinstance(data["keyword_exclude"], str) and data["keyword_exclude"] != "":
                    tempKeywordExclude = data["keyword_exclude"].split(",")

                last_craw_date = None

                if data["id"] != None:
                    last_craw_date = await keywordsService.get_last_craw_date(keyword_id=data["id"], source_id=transactionService.source_id_pantip)

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

            except Exception as e:
                lineNotify.send_notify_to_dev(
                    message=f"WARNING PANTIP:\n\n in loop format raw data \n\n {e}")

        # # * [NOTIFY]: Notify when have keyword to scraping
        # lineNotify.send_to_scraper_daily_data(
        #     message=f"Pantip\n\n มีการสั่งให้ทำงาน จำนวน:{len(search_data)} keyword."
        # )

        if len(search_data) > 0:
            try:
                formatted_search_data = dataFormat.format_keyword_group_by_campaign(
                    raw_data=search_data
                )

                await scraping_data(search_data=formatted_search_data, paging=paging)
            except Exception as e:
                lineNotify.send_notify_to_dev(
                    message=f"Pantip\n\n scraping not working \n\n {e}")
        else:
            lineNotify.send_to_scraper_process(
                message=f"Pantip\n\n ไม่พบ Keywords ที่ต้องการกวาดข้อมูล.")

        await set_process_status(
            status="0"
        )
    except Exception as e:
        lineNotify.send_to_scraper_problem(
            message=f"Pantip\n\n Error\n{e}.")
        await set_process_status(
            status="0"
        )
