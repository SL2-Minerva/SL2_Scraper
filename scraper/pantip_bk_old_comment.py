
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from datetime import datetime, timedelta

import random
import json
import time
import driver.main as driverInstant
import xpath.pantip as xpathPantip
import services.pantip_api as pantipService
import services.keywords as keywordsService
import services.transaction as transactionService
import modules.file_handle as fileHandle
import modules.segmentation as segmentation
import modules.line_notify as lineNotify
import formatters.line_format as lineFormat
import formatters.data_format as dataFormat
import helpers.scraper as scraperHelper
import helpers.error_handle as errorHandle


async def run():
    print("Pantip Scraper is running...")

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
            message_err = f"WARNING PANTIP:\n\n in loop format raw data \n\n {e}"
            lineNotify.send_notify_to_dev(message=message_err)

    if len(search_data) > 0:
        try:
            await scraping_data_with_keyword_and_or_not(search_data=search_data, paging=paging)
        except Exception as e:
            message_err = f"Pantip\n\n scraping not working \n\n {e}"
            lineNotify.send_notify_to_dev(message=message_err)
    else:
        message = f"Pantip\n\n ไม่พบ Keywords ที่ต้องการกวาดข้อมูล."
        lineNotify.send_notify_scraping_result(message=message)


async def scraping_data_with_keyword_and_or_not(search_data=[], paging=1):
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

    driver = result_create_driver['driver']
    transaction_success = 0
    round_of_scraping = 0

    datetime_start_scraping = datetime.now()

    # search_data_notify = []
    data_error = []

    # try:
    #     search_data_notify = dataFormat.format_notify_keyword_campaign(
    #         data=search_data)
    # except Exception as e:
    #     message_err = f"Pantip\n\n format_notify_keyword_campaign \n\n {e}"
    #     lineNotify.send_notify_to_dev(message=message_err)

    try:
        time_of_recreate_driver = result_create_driver['index']
        now_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        message = f"[RUN]\n\n Pantip Scraper:\n running at {now_datetime}\n time of recreate driver: {time_of_recreate_driver}\n search data count: {len(search_data)}\n\n"
        lineNotify.send_to_scraper_process(message=message)
    except Exception as e:
        pass

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

                err_message = f"WARNING [pantipScraper]:\n int(transaction_limit) \n\n {e}"
                lineNotify.send_to_scraper_problem(message=err_message)

            try:
                transaction_remaining = int(transaction_remaining)
            except Exception as e:
                transaction_remaining = -1

                err_message = f"WARNING [pantipScraper]:\n int(transaction_remaining) \n\n {e}"
                lineNotify.send_to_scraper_problem(message=err_message)

            # TODO: condition 1 check in range date
            if not scraperHelper.is_in_range_date(start_at=start_at, end_at=end_at):
                # search_data_notify = dataFormat.set_campaign_condition_result(
                #     campaign_name_to_find=campaign_name,
                #     condition_to_find="condition_1",
                #     condition_result="No",
                #     data=search_data_notify
                # )
                continue
            else:
                # search_data_notify = dataFormat.set_campaign_condition_result(
                #     campaign_name_to_find=campaign_name,
                #     condition_to_find="condition_1",
                #     condition_result="Yes",
                #     data=search_data_notify
                # )
                pass

            # TODO: condition 2 check limit transaction remaining
            if not scraperHelper.is_in_transaction_limit(transaction_limit=transaction_limit, transaction_remaining=transaction_remaining):
                # search_data_notify = dataFormat.set_campaign_condition_result(
                #     campaign_name_to_find=campaign_name,
                #     condition_to_find="condition_2",
                #     condition_result="No",
                #     data=search_data_notify
                # )
                continue
            else:
                # search_data_notify = dataFormat.set_campaign_condition_result(
                #     campaign_name_to_find=campaign_name,
                #     condition_to_find="condition_2",
                #     condition_result="Yes",
                #     data=search_data_notify
                # )
                pass

            # TODO: condition 3 check frequency
            if not scraperHelper.is_out_of_frequency(frequency_minute=frequency, last_craw_date=last_craw_date):
                # search_data_notify = dataFormat.set_campaign_condition_result(
                #     campaign_name_to_find=campaign_name,
                #     condition_to_find="condition_3",
                #     condition_result="No",
                #     data=search_data_notify
                # )
                continue
            else:
                # search_data_notify = dataFormat.set_campaign_condition_result(
                #     campaign_name_to_find=campaign_name,
                #     condition_to_find="condition_3",
                #     condition_result="Yes",
                #     data=search_data_notify
                # )
                pass

            # list ["main_keyword", "and_keyword", "or_keyword"]
            keywords = search["keyword"]
            keyword_exclude = search["keyword_exclude"]

            number_of_result = 0

            for keyword in keywords:
                url = f"https://pantip.com/search?q={keyword}&timebias=true"

                topic_url = []
                data_result = []

                try:
                    driver.get(url)

                    wait = WebDriverWait(driver, 15)

                    print("Wait for post link...")
                    wait.until(EC.presence_of_element_located(
                        (By.XPATH, xpathPantip.post_link())))

                    # scroll to bottom
                    for i in range(0, paging):
                        print(f"Scroll to bottom: {i}")

                        driver.execute_script(
                            "window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(2)

                    post_link = driver.find_elements(
                        "xpath", xpathPantip.post_link())

                    for link in post_link:
                        topic_url.append(link.get_attribute("href"))

                    for temp_url in topic_url:
                        try:
                            post_result = await get_post_detail_and_comments(topic_url=temp_url, driver=driver, keyword_check=keywords, keyword_exclude=keyword_exclude)
                            data_result.extend(post_result)
                        except Exception as e:
                            lineNotify.send_notify_to_dev(
                                message=f"Pantip\n\n error on for url in topic_url: {temp_url}\n\n {e}")
                            # result_create_driver2 = create_my_driver(0)
                            # driver = result_create_driver2['driver']

                            # try:
                            #     time_of_recreate_driver2 = result_create_driver2['index']
                            #     now_datetime2 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                            #     driver_session_id = driver.session_id

                            #     err_message = f"[RE-RUN]\n\n Pantip Scraper:\n\n running at {now_datetime2}\n\n time of recreate driver: {time_of_recreate_driver2}\n\n session id:{driver_session_id}\n\n"
                            #     lineNotify.send_to_scraper_process(
                            #         message=err_message)

                            #     post_result = await get_post_detail_and_comments(topic_url=temp_url, driver=driver, keyword_check=keywords, keyword_exclude=keyword_exclude)
                            #     data_result.extend(post_result)
                            # except Exception as e:
                            #     lineNotify.send_notify_to_dev(
                            #         message=f"WARNING PANTIP for url in topic_url: {temp_url}\n\n {e}")

                    print(f"post count: {len(topic_url)}")

                    # # todo: insert to database
                    # if len(data_result) > 0:
                    #     await pantipService.updatePostsAndCommentsData(data=data_result, campaign_id=campaign_id, keyword_id=keyword_id)

                    # # todo: send line notify
                    # try:
                    #     message = lineFormat.format_line_scraping_result(
                    #         platform="Pantip",
                    #         campaign_name=campaign_name,
                    #         keyword_name=keyword,
                    #         count_activity=len(data_result)
                    #     )

                    #     lineNotify.send_to_scraper_daily_data(
                    #         message=message)
                    # except Exception as e:
                    #     err_message = f"Pantip\n\n error send line notify\n Url: {url} \n\n {e}"
                    #     lineNotify.send_notify_to_dev(message=err_message)

                    number_of_result += len(data_result)

                except Exception as e:
                    result_message = errorHandle.handle(e)

                    if result_message["is_error"]:
                        if "ส่งถึง Developer" in result_message['message']:
                            msg = f"Pantip\n\nPost not found with keyword:\n{keyword}\n\n{result_message['message']}"
                            lineNotify.send_notify_to_dev(message=msg)
                        else:
                            data_error = dataFormat.set_keyword_error(
                                data=data_error, type_error=result_message['message'], keyword=keyword)

                # # TODO: set keyword result to line notify
                # try:
                #     search_data_notify = dataFormat.set_keyword_result(
                #         data=search_data_notify,
                #         campaign_name_to_find=campaign_name,
                #         keyword_to_find=keyword,
                #         number_of_result=len(data_result))
                # except Exception as e:
                #     message = f"Pantip\n\n error on set_keyword_result\n\n {e}"
                #     lineNotify.send_notify_to_dev(message=message)

            await transactionService.pushTransactionScrapingResult(
                keyword_id=keyword_id,
                source_id=transactionService.source_id_pantip,
                number_of_result=number_of_result,
                organization_id=organization_id
            )

            transaction_success += 1

        except Exception as e:
            message_err = f"Pantip\n\n for search in search_data ทำงานผิดปกติ \n\n {e}"
            lineNotify.send_notify_to_dev(message=message_err)

    try:
        driver.close()
        driver.quit()
    except Exception as e:
        pass

    if len(data_error) > 0:
        try:
            message_err = "Pantip Warning.\n\n"
            i = 0

            for err in data_error:
                i += 1
                message_err += f'{i}. Error:{err["type_error"]}\nKeyword: {", ".join(err["keywords"])}\n\n'

            lineNotify.send_to_scraper_problem(message=message_err)
        except Exception as e:
            message_err = f"Pantip\n\n error in data_error \n\n {e}"
            lineNotify.send_to_scraper_problem(message=message_err)

    try:
        datetime_end_scraping = datetime.now()
        datetime_diff = datetime_end_scraping - datetime_start_scraping
        diff_string = dataFormat.format_time_diff(
            diff_sec=datetime_diff.total_seconds())

        # message_search_data_result = dataFormat.format_line_notify_result(
        #     data=search_data_notify)

        message2 = f'[FINISH]\nat {datetime_end_scraping.strftime("%Y-%m-%d %H:%M")}\n Pantip\n\ntime of scraping:\n{diff_string}\n\nround of scraping:{round_of_scraping}\nsuccess:{transaction_success}'
        lineNotify.send_to_scraper_process(message=message2)
    except Exception as e:
        message2 = f"[FINISH][ERROR]\n\n Pantip\n\nerror:\n{e}\n\n"
        lineNotify.send_to_scraper_process(message=message2)


async def get_post_detail_and_comments(topic_url="", driver=None, keyword_check=[], keyword_exclude=[]):
    print(f"{topic_url}")

    driver.get(topic_url)

    wait = WebDriverWait(driver, 30)

    data = []

    is_pass = True
    is_excluded = False

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
                "images": content_images,
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
                (By.XPATH, xpathPantip.comment_content())))

            comments_content = driver.find_elements(
                "xpath", xpathPantip.comment_content())

            comments_account_name = driver.find_elements(
                "xpath", xpathPantip.comment_account_name())
            comments_datetime = driver.find_elements(
                "xpath", xpathPantip.comment_datetime())
            comments_like = driver.find_elements(
                "xpath", xpathPantip.comment_like())

            for i in range(0, len(comments_content)):
                comment_is_pass = True
                comment_is_excluded = False

                try:
                    # handle case user profile is icon/image
                    try:
                        comment_account_name = comments_account_name[i].get_attribute(
                            "textContent").replace("\t", "").replace("\n", "")
                    except Exception as e:
                        comment_account_name = ""

                    try:
                        full_text = comments_content[i].get_attribute(
                            "textContent").replace("\t", "").replace("\n", "")
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
                            post_date = comments_datetime[i].get_attribute(
                                "data-utime").replace("\t", "").replace("\n", "")
                        except Exception as e:
                            post_date = "null"

                        try:
                            comment_like = comments_like[i].get_attribute(
                                "textContent").replace("\t", "").replace("\n", "")
                        except Exception as e:
                            comment_like = "0"

                        data.append({
                            "full_text":  f"{full_text}",
                            "message_type": "comment",
                            "url": f"{topic_url}",
                            "author": f"{comment_account_name}",
                            "post_date": f"{post_date}",
                            "like": comment_like
                        })
                except Exception as e:
                    message = f"Pantip\n\n error at comments_content: {topic_url}\n\n {e}"
                    lineNotify.send_notify_to_dev(message)
        except Exception as e:
            pass

    print(f"activity count: {len(data)}")

    return data
