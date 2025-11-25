from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver

from datetime import datetime, timedelta
from numerize import numerize

import time
import envconstant.env as env
import driver.main as driverInstant
import xpath.twitter as xpathTwitter
import services.twitter as twitterService
import services.keywords as keywordsService
import services.transaction as transactionService
import formatters.twitter_format as twitterFormat
import formatters.line_format as lineFormat
import formatters.data_format as dataFormat
import modules.file_handle as fileHandle
import modules.segmentation as segmentation
import modules.line_notify as lineNotify
import helpers.scraper as scraperHelper
import helpers.twitter as twitterHelper
import helpers.error_handle as errorHandle
import helpers.number as numberHelper


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
        lineNotify.send_to_scraper_problem(message=message_err)

        return False


async def set_process_status(status="0"):
    try:
        await fileHandle.write_process_status(
            status=status, platform=fileHandle.process_twitter)
    except Exception as e:
        message_err = f"Twitter\n\n error on set_process_status\n\n {e}"
        lineNotify.send_to_scraper_problem(message=message_err)


async def scraping_data(search_data=[], paging=1):
    def create_my_driver(index=0):
        try:
            time.sleep(3)

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

    twitter_driver = result_create_driver['driver']
    twitter_wait = WebDriverWait(twitter_driver, 10)

    is_login = False
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
                source_id=transactionService.source_id_twitter
            )

            number_of_result = 0
            flag_error = []

            for keyword in keywords:
                temp_keywords.append(f"{keyword}({keyword_id})")

                url = f"https://x.com/search?q={keyword}&src=typed_query&f=live"

                post_link = []
                topic_url = []
                data_result = []

                try:
                    twitter_driver.get(url)

                    try:
                        if not is_login:
                            await login(driver=twitter_driver, wait=twitter_wait)
                            is_login = True

                            time.sleep(3)
                            twitter_driver.get(url)

                    except Exception as e:
                        pass

                    for _ in range(0, paging):
                        try:
                            twitter_wait.until(EC.presence_of_element_located(
                                (By.XPATH, xpathTwitter.post_link())))

                            post_link = twitter_driver.find_elements(
                                "xpath", xpathTwitter.post_link())

                            for link in post_link:
                                try:
                                    topic_url.append(
                                        link.get_attribute("href"))

                                except Exception as e:
                                    print("link not have href")

                        except Exception as e:
                            pass

                        twitter_driver.execute_script(
                            "window.scrollTo(0, document.body.scrollHeight);")

                        time.sleep(2)

                    topic_url = list(set(topic_url))

                    for url in topic_url:
                        try:
                            post_result = await get_post_detail_and_comments(
                                keyword__id=keyword_id,
                                topic_url=url,
                                driver=twitter_driver,
                                keyword_check=keywords,
                                keyword_exclude=keyword_excludes
                            )
                            data_result.extend(post_result)

                        except Exception as e:
                            # todo: =============> START: handle error <============
                            try:
                                result_message = errorHandle.handle(e)

                                if result_message["is_error"]:
                                    if "ส่งถึง Developer" in result_message['message']:
                                        msg = f"Twitter\n\nerror on [for url in topic_url]:\n{keyword}\n\n{result_message['message']}"
                                        lineNotify.send_notify_to_dev(
                                            message=msg)

                                        flag_error.append(
                                            "เว็บไซต์ปลายทางไม่ตอบสนองในขณะนั้น หรือเกิน Litmit ต่อวันที่รับได้")
                                    else:
                                        flag_error.append(
                                            result_message['message'])

                            except Exception as ee:
                                message_err = f"Twitter\n\n error on errorHandle at [error on for url in topic_url]\n\n {ee}"
                                lineNotify.send_to_scraper_problem(
                                    message=message_err)
                            # todo: =============> END: handle error <============

                    number_of_result += len(data_result)

                    # todo: insert to database
                    if len(data_result) > 0:
                        await transactionService.insert_post_and_comments_data_to_mysql(new_data=data_result)
                        # await transactionService.updatePostsAndCommentsData(
                        #     data=data_result,
                        #     collection_name=transactionService.collection_name_twitter,
                        #     campaign_id=campaign_id,
                        #     keyword_id=keyword_id
                        # )

                except Exception as e:
                    # todo: =============> START: handle error <============
                    try:
                        result_message = errorHandle.handle(e)

                        if result_message["is_error"]:
                            if "ส่งถึง Developer" in result_message['message']:
                                msg = f"Twitter\n\nPost not found with keyword:\n{keyword}\n\n{result_message['message']}"
                                lineNotify.send_notify_to_dev(message=msg)

                                flag_error.append(
                                    "เว็บไซต์ปลายทางไม่ตอบสนองในขณะนั้น หรือเกิน Litmit ต่อวันที่รับได้")
                            else:
                                flag_error.append(
                                    f"{result_message['message']}")

                    except Exception as ee:
                        message_err = f"Twitter\n\n error on errorHandle\n\n {ee}"
                        lineNotify.send_to_scraper_problem(
                            message=message_err)

                    # todo: =============> END: handle error <============

            flag_error_message = ""

            try:
                if number_of_result == 0:
                    flag_error = list(set(flag_error))
                    flag_error_message = ", ".join(flag_error)

            except Exception as e:
                lineNotify.send_to_scraper_problem(
                    message=f"Twitter\n\n error on set flag_error_message\n\n {e}")

            await transactionService.pushTransactionScrapingResult(
                keyword_id=keyword_id,
                source_id=transactionService.source_id_twitter,
                number_of_result=number_of_result,
                organization_id=organization_id,
                flag_error=flag_error_message
            )

            total_result += number_of_result

        datetime_end_campaign_scraping = datetime.now()
        keyword_str = ", ".join(temp_keywords)

        # * Notify when have keyword to scraping
        # * Notify when have keyword to scraping
        if len(temp_keywords) > 0:
            try:
                line_message = lineFormat.format_campaign_result(
                    platform="Twitter",
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
                    message=f"[FINISH][ERROR]\n\nTwitter\n\nerror:\n{e}")

        try:
            datetime_diff = datetime_end_campaign_scraping - datetime_start_campaign_scraping
            diff_string = dataFormat.format_time_diff(
                diff_sec=datetime_diff.total_seconds())

            await fileHandle.push_log_csv_file(
                platform="twitter",
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
                message=f"Twitter\n\n error on push_log_csv_file\n\n {e}")

        time.sleep(2)

    try:
        twitter_driver.close()
        twitter_driver.quit()
    except Exception as e:
        pass


async def get_post_detail_and_comments(keyword__id="", topic_url="", driver=None, keyword_check=[], keyword_exclude=[]):
    data = []

    try:
        driver.get(topic_url)
        wait = WebDriverWait(driver, 15)

        is_excluded = False
        is_pass = True

        try:
            tweet_id = topic_url.split("/")[-1]
        except Exception as e:
            tweet_id = None

        try:
            time.sleep(3)

            wait.until(EC.presence_of_element_located(
                (By.XPATH, xpathTwitter.post_datetime())))

            content = driver.find_element(
                By.XPATH, xpathTwitter.post_detail()).get_attribute("textContent").replace("\t", "").replace("\n", "")

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
                # try:
                #     account_name = driver.find_element(
                #         By.XPATH, xpathTwitter.post_account_name()).get_attribute("textContent")
                # except Exception as e:
                #     account_name = "null"

                try:
                    profile_image = driver.find_element(
                        By.XPATH, xpathTwitter.post_account_profile_img()).get_attribute("src")
                except Exception as e:
                    profile_image = "null"

                try:
                    screen_name = driver.find_element(
                        By.XPATH, xpathTwitter.post_screen_name()).get_attribute("textContent").replace("\t", "").replace("\n", "").replace("@", "")
                except Exception as e:
                    screen_name = "null"

                try:
                    post_datetime = driver.find_element(
                        By.XPATH, xpathTwitter.post_datetime()).get_attribute("datetime")

                    temp_datetime = datetime.strptime(
                        post_datetime, "%Y-%m-%dT%H:%M:%S.%fZ") + timedelta(hours=7)

                    post_datetime = temp_datetime.strftime(
                        "%a %b %d %H:%M:%S +0000 %Y")
                except Exception as e:
                    post_datetime = "null"

                try:
                    post_images_ele = driver.find_elements(
                        By.XPATH, xpathTwitter.post_detail_image())
                except Exception as e:
                    post_images_ele = []

                try:
                    like = driver.find_element(
                        By.XPATH, xpathTwitter.post_like()).get_attribute("aria-label").replace(" ", "").replace(".", "").replace("Like", "").replace("like", "").replace("s", "")
                except Exception as e:
                    like = 0

                try:
                    retweet = driver.find_element(
                        By.XPATH, xpathTwitter.post_retweet()).get_attribute("aria-label").replace(" ", "").replace(".", "").replace("R", "").replace("r", "").replace("epost", "").replace("s", "")
                except Exception as e:
                    retweet = 0

                try:
                    reply_count = driver.find_element(
                        By.XPATH, xpathTwitter.post_reply_count()).get_attribute("aria-label").replace(" ", "").replace(".", "").replace("replies", "").replace("Replies", "").replace('Reply', "").replace('reply', "").replace("s", "")
                except Exception as e:
                    reply_count = 0

                try:
                    bookmark_count = driver.find_element(
                        By.XPATH, xpathTwitter.post_bookmark_count()).get_attribute("aria-label").replace(" ", "").replace(".", "").replace("Bookmark", "").replace("bookmark", "").replace('s', "")
                except Exception as e:
                    bookmark_count = 0

                try:
                    view_count = driver.find_element(
                        By.XPATH, xpathTwitter.post_view())
                    view_count = numberHelper.denumerize(view_count.text)
                except Exception as e:
                    er_message = f"Twitter\n error on get view count\n{e}"
                    lineNotify.send_to_scraper_process(message=er_message)
                    view_count = 0

                content_images = []
                for image in post_images_ele:
                    try:
                        content_images.append(image.get_attribute("src"))
                    except Exception as e:
                        pass

                data.append(twitterFormat.format_data_for_mysql(
                    keyword_id=keyword__id,
                    tweet_id=tweet_id,
                    ref_id="",
                    topic_url=topic_url,
                    full_text=content,
                    post_datetime=post_datetime,
                    content_images=content_images,
                    profile_image=profile_image,
                    screen_name=screen_name,
                    message_type="Post",
                    reply_count=reply_count,
                    retweet_count=retweet,
                    bookmark_count=bookmark_count,
                    favorite_count=like,
                    view_count=view_count,
                ))
                # data.append(twitterFormat.format_data_tweet(
                #     id_str=tweet_id,
                #     full_text=content,
                #     name=account_name,
                #     screen_name=screen_name,
                #     created_at=post_datetime,
                #     source=topic_url,
                #     favorite_count=like,
                #     retweet_count=retweet,
                #     message_type="post",
                #     profile_image=profile_image,
                #     content_images=content_images,
                #     reply_count=reply_count,
                #     bookmark_count=bookmark_count,
                #     view_count=view_count,
                # ))

        except Exception as e:
            data_return = None
            data_return = await get_post_detail_from_api(
                topic_url=topic_url,
                keyword_check=keyword_check,
                keyword_exclude=keyword_exclude
            )

            if data_return is not None:
                data.append(twitterFormat.format_data_for_mysql(
                    keyword_id=keyword__id,
                    tweet_id=data_return.get("id_str") or None,
                    ref_id="",
                    topic_url=data_return.get("source") or None,
                    full_text=data_return.get("full_text") or None,
                    post_datetime=data_return.get("created_at") or None,
                    content_images=data_return.get("content_images") or [],
                    profile_image=data_return.get(
                        "user").get("profile_image") or None,
                    screen_name=data_return.get(
                        "user").get("screen_name") or None,
                    message_type="Post",
                    reply_count=data_return.get("reply_count") or 0,
                    retweet_count=data_return.get("retweet_count") or 0,
                    bookmark_count=data_return.get("bookmark_count") or 0,
                    favorite_count=data_return.get("favorite_count") or 0,
                    view_count=data_return.get("view_count") or 0,
                ))
                # data.append(data_return)

        if (not is_excluded) and is_pass:
            try:
                wait.until(EC.presence_of_element_located(
                    (By.XPATH, xpathTwitter.comment_box_content())))

                driver.execute_script(
                    "window.scrollTo(0, 2400);")
                time.sleep(3)

                comments_boxs = driver.find_elements(
                    By.XPATH, xpathTwitter.comment_box_content())

                for i in range(0, len(comments_boxs)):
                    comment_is_pass = True  # ของเดิมเป็น False หากเปิดใช้งานการตรวจสอบเงือนไข
                    comment_is_excluded = False

                    try:
                        comment_tweet_link = driver.find_element(
                            By.XPATH, xpathTwitter.comment_link(only_xpath=False, length=i+1))

                        comment_content = driver.find_element(
                            By.XPATH, xpathTwitter.comment_content(only_xpath=False, length=i+1))

                        comment_account_name = driver.find_element(
                            By.XPATH, xpathTwitter.comment_account_name(only_xpath=False, length=i+1))

                        comment_account_profile_img = driver.find_element(
                            By.XPATH, xpathTwitter.comment_account_profile_img(only_xpath=False, length=i+1))

                        comment_screen_name = driver.find_element(
                            By.XPATH, xpathTwitter.comment_screen_name(only_xpath=False, length=i+1))

                        comment_datetime = driver.find_element(
                            By.XPATH, xpathTwitter.comment_datetime(only_xpath=False, length=i+1))

                        comment_like = driver.find_element(
                            By.XPATH, xpathTwitter.comment_like(only_xpath=False, length=i+1))

                        comment_retweet = driver.find_element(
                            By.XPATH, xpathTwitter.comment_retweet(only_xpath=False, length=i+1))

                        comment_reply = driver.find_element(
                            By.XPATH, xpathTwitter.comment_reply(only_xpath=False, length=i+1))

                        comment_view = driver.find_element(
                            By.XPATH, xpathTwitter.comment_view(only_xpath=False, length=i+1))

                    except Exception as e:
                        continue

                    try:
                        # handle case user profile is icon/image
                        try:
                            comment_account_name = comment_account_name.get_attribute(
                                "textContent").replace("\t", "").replace("\n", "")
                        except Exception as e:
                            comment_account_name = "null"

                        try:
                            comment_account_profile_img = comment_account_profile_img.get_attribute(
                                "src")
                        except Exception as e:
                            comment_account_profile_img = "null"

                        try:
                            comment_screen_name = comment_screen_name.get_attribute(
                                "textContent").replace("\t", "").replace("\n", "").replace("@", "")
                        except Exception as e:
                            comment_screen_name = "null"

                        try:
                            comment_datetime = comment_datetime.get_attribute(
                                "datetime").replace("\t", "").replace("\n", "")

                            temp_comment_datetime = datetime.strptime(
                                comment_datetime, "%Y-%m-%dT%H:%M:%S.%fZ") + timedelta(hours=7)

                            comment_datetime = temp_comment_datetime.strftime(
                                "%a %b %d %H:%M:%S +0000 %Y")

                        except Exception as e:
                            comment_datetime = "null"

                        try:
                            full_text = comment_content.get_attribute(
                                "textContent").replace("\t", "").replace("\n", "")
                        except Exception as e:
                            full_text = "null"

                        # # เมื่อมีคำใดคำหนึ่งใน keyword exclude อยู่ใน content หรือ title จะไม่เก็บข้อมูล
                        # if len(keyword_exclude) > 0:
                        #     comment_is_excluded = any(
                        #         (keyword_not in full_text) for keyword_not in keyword_exclude)

                        # # ใน full_text จะต้องมีทุกคำที่ต้องการ ถึงจะนำไปเก็บข้อมูล
                        # if len(keyword_check) > 0:
                        #     comment_is_pass = all((segmentation.compare_text_segmenting_all(text=full_text, keyword=keyword))
                        #                           for keyword in keyword_check)

                        # if full_text == "" or full_text == " " or full_text == None:
                        #     comment_is_pass = False

                        if (not comment_is_excluded) and comment_is_pass:
                            try:
                                comment_like = int(comment_like.get_attribute(
                                    "textContent").replace("\t", "").replace("\n", ""))
                            except Exception as e:
                                comment_like = 0

                            try:
                                comment_retweet = int(comment_retweet.get_attribute(
                                    "textContent").replace("\t", "").replace("\n", ""))
                            except Exception as e:
                                comment_retweet = 0

                            try:
                                comment_reply = int(comment_reply.get_attribute(
                                    "aria-label").replace("Replie", "").replace("Reply", "").replace("replies", "").replace("reply", "").replace(" ", "").replace(".", "").replace("s", "").replace("\t", "").replace("\n", ""))
                            except Exception as e:
                                comment_reply = 0

                            try:
                                comment_view = int(comment_view.get_attribute(
                                    "aria-label").replace("views", "").replace("View", "").replace("post", "").replace("analytics", "").replace(" ", "").replace(".", "").replace("\t", "").replace("\n", ""))
                            except Exception as e:
                                comment_view = 0

                            try:
                                comment_url = comment_tweet_link.get_attribute(
                                    "href")
                            except Exception as e:
                                comment_url = "null"

                            try:
                                comment_tweet_id = comment_url.split("/")[-1]
                            except Exception as e:
                                comment_tweet_id = "null"

                            try:
                                content_images_ele = driver.find_elements(
                                    By.XPATH,
                                    xpathTwitter.comment_content_photo(
                                        only_xpath=False,
                                        length=i+1
                                    )
                                )
                            except Exception as e:
                                content_images_ele = []

                            comment_images = []
                            for image in content_images_ele:
                                try:
                                    comment_images.append(
                                        image.get_attribute("src"))
                                except Exception as e:
                                    pass

                            data.append(twitterFormat.format_data_for_mysql(
                                keyword_id=keyword__id,
                                tweet_id=comment_tweet_id,
                                ref_id=tweet_id,
                                topic_url=comment_url,
                                full_text=full_text or None,
                                post_datetime=comment_datetime,
                                content_images=comment_images,
                                profile_image=comment_account_profile_img,
                                screen_name=comment_screen_name,
                                message_type="Comment",
                                reply_count=comment_reply,
                                retweet_count=comment_retweet,
                                bookmark_count=0,
                                favorite_count=comment_like,
                                view_count=comment_view,
                            ))

                            # data.append(twitterFormat.format_data_tweet(
                            #     id_str=tweet_id,
                            #     full_text=full_text,
                            #     name=comment_account_name,
                            #     screen_name=comment_screen_name,
                            #     created_at=comment_datetime,
                            #     source=comment_url,
                            #     favorite_count=comment_like,
                            #     retweet_count=comment_retweet,
                            #     message_type="comment",
                            #     profile_image=comment_account_profile_img,
                            #     content_images=comment_images,
                            #     reply_count=comment_reply,
                            #     bookmark_count=0,
                            #     view_count=comment_view,
                            # ))

                    except Exception as e:
                        lineNotify.send_notify_to_dev(
                            message=f"WARNING TWITTER AT get comment: {topic_url} {e}")

            except Exception as e:
                pass

    except Exception as e:
        data_return = None
        data_return = await get_post_detail_from_api(
            topic_url=topic_url,
            keyword_check=keyword_check,
            keyword_exclude=keyword_exclude
        )

        if data_return is not None:
            data.append(twitterFormat.format_data_for_mysql(
                keyword_id=keyword__id,
                tweet_id=data_return.get("id_str") or None,
                ref_id="",
                topic_url=data_return.get("source") or None,
                full_text=data_return.get("full_text") or None,
                post_datetime=data_return.get("created_at") or None,
                content_images=data_return.get("content_images") or [],
                profile_image=data_return.get(
                        "user").get("profile_image") or None,
                screen_name=data_return.get(
                    "user").get("screen_name") or None,
                message_type="Post",
                reply_count=data_return.get("reply_count") or 0,
                retweet_count=data_return.get("retweet_count") or 0,
                bookmark_count=data_return.get("bookmark_count") or 0,
                favorite_count=data_return.get("favorite_count") or 0,
                view_count=data_return.get("view_count") or 0,
            ))
            # data.append(data_return)

    return data


async def get_post_detail_from_api(topic_url="", keyword_check=[], keyword_exclude=[]):
    data_return = None

    try:
        data_result = twitterHelper.get_tweet_data_api(url=topic_url)

        if data_result is not None:
            twitter_data = twitterFormat.format_data_fx_tweet(
                data=data_result
            )

            is_pass_2 = False
            is_excluded_2 = False

            content = twitter_data["full_text"]

            # * เมื่อมีคำใดคำหนึ่งใน keyword exclude อยู่ใน content หรือ title จะไม่เก็บข้อมูล
            if len(keyword_exclude) > 0:
                is_excluded_2 = any((keyword_not in content)
                                    for keyword_not in keyword_exclude)

            # * ใน content จะต้องมีทุกคำที่ต้องการ ถึงจะนำไปเก็บข้อมูล
            if len(keyword_check) > 0:
                is_pass_2 = all(segmentation.compare_text_segmenting_all(
                    text=content, keyword=keyword) for keyword in keyword_check)

            if content == "" or content == " " or content == None:
                is_pass_2 = False

            if (not is_excluded_2) and is_pass_2:
                data_return = twitter_data

    except Exception as e:
        pass

    return data_return


async def login(driver, wait):
    wait.until(EC.presence_of_element_located(
        (By.XPATH, xpathTwitter.next_button())))
    time.sleep(1)
    next_button = driver.find_element(
        By.XPATH, xpathTwitter.next_button())
    time.sleep(2)

    print("Login...")

    username = env.TWITTER_USERNAME_2
    password = env.TWITTER_PASSWORD_2

    now = datetime.now()

    if now.hour >= 14:
        username = env.TWITTER_USERNAME_2
        password = env.TWITTER_PASSWORD_2
    elif now.hour >= 8:
        username = env.TWITTER_USERNAME_1
        password = env.TWITTER_PASSWORD_1

    try:
        wait.until(EC.presence_of_element_located(
            (By.XPATH, xpathTwitter.username_input())))

        wait.until(EC.presence_of_element_located(
            (By.XPATH, xpathTwitter.next_button())))

        time.sleep(1)

        username_input = driver.find_element(
            By.XPATH, xpathTwitter.username_input())
        username_input.send_keys(username)
        next_button = driver.find_element(
            By.XPATH, xpathTwitter.next_button())

        time.sleep(1)
        next_button.click()

        wait.until(EC.presence_of_element_located(
            (By.XPATH, xpathTwitter.password_input())))

        password_input = driver.find_element(
            By.XPATH, xpathTwitter.password_input())
        password_input.send_keys(password)

        wait.until(EC.presence_of_element_located(
            (By.XPATH, xpathTwitter.login_button())))

        login_button = driver.find_element(
            By.XPATH, xpathTwitter.login_button())

        time.sleep(2)
        login_button.click()

        print("Login Finish.")
    except Exception as e:
        lineNotify.send_notify_to_dev(
            message=f"WARNING TWITTER AT login: {e}")
        print(f"Notice: Login fail.")


async def run():
    try:
        print("Twitter Scraper is started")

        if await check_process_running():
            print("Twitter have process running already. Exit.")

            lineNotify.send_to_scraper_daily_data(
                message=f"Twitter\n\n มีกระบวนการกวาดข้อมูลทำงานอยู่แล้ว."
            )

            await set_process_status(
                status="0"
            )
            exit()

        else:
            print("Twitter Scraper is continue running.")
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
                    last_craw_date = await keywordsService.get_last_craw_date(keyword_id=data["id"], source_id=transactionService.source_id_twitter)

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
                    "keyword": tempKeyword,
                    "keyword_exclude": tempKeywordExclude,
                    "last_crawed_at": last_craw_date,
                })
            except Exception as e:
                lineNotify.send_notify_to_dev(
                    message=f"WARNING twitter:\n\n in loop format raw data \n\n {e}")

        if len(search_data) > 0:
            try:
                formatted_search_data = dataFormat.format_keyword_group_by_campaign(
                    raw_data=search_data
                )

                await scraping_data(search_data=formatted_search_data, paging=paging)
            except Exception as e:
                lineNotify.send_notify_to_dev(
                    message=f"Twitter\n\n scraping not working \n\n {e}")

        else:
            lineNotify.send_notify_scraping_result(
                message=f"Twitter\n\n ไม่พบ Keywords ที่ต้องการกวาดข้อมูล.")
    except Exception as e:
        lineNotify.send_to_scraper_problem(
            message=f"Twitter\n\n Error\n{e}.")

    await set_process_status(
        status="0"
    )
