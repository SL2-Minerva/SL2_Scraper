from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver

from datetime import datetime, timedelta

import json
import time
import envconstant.env as env
import driver.main_test as driverInstant
import xpath.twitter as xpathTwitter
import formatters.twitter_format as twitterFormat
import formatters.line_format as lineFormat
import modules.segmentation as segmentation
import modules.line_notify as lineNotify
import modules.file_handle as fileHandle
# import services.keywords_test as keywordsService
import helpers.twitter as twitterHelper
import helpers.number as numberHelper
import services.transaction as transactionService

# AAAAAAAAAAAAAAAAAAAAABTzxgEAAAAAAruhD9x0bdikiKWirHn1ekLCFSM%3Dui806f31rvmd6I7zJcJXvHdXLKlbKcPuej6HvYmbVliGGn1Bkx


# client_id = "UmtWMlp2X2ZwZWF6UmVORGxHUzI6MTpjaQ"
# client_secret = "qj6LFx3O-ZHLngCV9vK1Bmq8BADXsqFIOGs8z2BpWo6UubFi5p"

# access_token="1702178723955630080-15ByzGQQ0qtIJKMKRCchhVhZ4C1o42"
# access_token_secret="jFFDuWHVRmGsAn6K7vvvsBlCPPYn14QZuQBET04uCq4Pj"

# async def run():
#     paging = driverInstant.get_paging_from_argv()
#     print(f"paging: {paging}")

#     raw_data = await keywordsService.getActiveKeyword()
#     search_data = []

#     for data in raw_data:
#         tempKeyword = []
#         tempKeywordExclude = []

#         if isinstance(data["name"], str) and data["name"] != "":
#             tempKeyword = data["name"].split(",")

#         if isinstance(data["keyword_exclude"], str) and data["keyword_exclude"] != "":
#             tempKeywordExclude = data["keyword_exclude"].split(",")

#         last_craw_date = None

#         if data["id"] != None:
#             last_craw_date = await keywordsService.get_last_craw_date(keyword_id=data["id"], source_id=transactionService.source_id_twitter)

#         search_data.append({
#             "keyword_id": data["id"],
#             "campaign_id": data["campaign_id"],
#             "campaign_name": data['campaign_name'],
#             "organization_id": data["organization_id"],
#             "start_at": data["start_at"],
#             "end_at": data["end_at"],
#             "frequency": data["frequency"],
#             "transaction_limit": data["transaction_limit"],
#             "transaction_reamining": data["transaction_reamining"],
#             "last_crawed_at": last_craw_date,
#             "keyword": tempKeyword,
#             "keyword_exclude": tempKeywordExclude,
#         })

#     await scraping_data_with_keyword_and_or_not(search_data=search_data, paging=paging)


async def scraping_data_with_keyword_and_or_not(search_data=[], paging=1):
    driver = driverInstant.create_driver()
    try:

        is_login = False

        for search in search_data:
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

            print("\n\n call condition")

            try:
                transaction_limit = int(transaction_limit)
            except Exception as e:
                transaction_limit = 0

                err_message = f"WARNING [twitterScraper]:\n int(transaction_limit) \n\n {e}"
                lineNotify.send_notify_to_dev(message=err_message)

            try:
                transaction_remaining = int(transaction_remaining)
            except Exception as e:
                transaction_remaining = -1

                err_message = f"WARNING [twitterScraper]:\n int(transaction_remaining) \n\n {e}"
                lineNotify.send_notify_to_dev(message=err_message)

            print("call condition 1")
            # TODO: condition 1 check in range date
            # if not scraperHelper.is_in_range_date(start_at=start_at, end_at=end_at):
            #     continue

            print("call condition 2")
            # TODO: condition 2 check limit transaction remaining
            # if not scraperHelper.is_in_transaction_limit(transaction_limit=transaction_limit, transaction_remaining=transaction_remaining):
            #     continue

            print("call condition 3")
            # TODO: condition 3 check frequency
            # if not scraperHelper.is_out_of_frequency(frequency_minute=frequency, last_craw_date=last_craw_date):
            #     continue

            print("Pass condition")
            keywords = search["keyword"]
            keyword_exclude = search["keyword_exclude"]

            number_of_result = 0

            for keyword in keywords:
                url = f"https://twitter.com/search?q={keyword}&src=typed_query"

                driver.get(url)
                try:
                    wait = WebDriverWait(driver, 10)

                    try:
                        if not is_login:
                            await login(driver=driver, wait=wait)
                            is_login = True

                            time.sleep(3)
                            driver.get(url)
                    except Exception as e:
                        print(f"WARNING: login exception: {e}")
                        pass

                    print("Wait for post link...")
                    post_link = []
                    topic_url = []

                    wait.until(EC.presence_of_element_located(
                        (By.XPATH, xpathTwitter.post_link())))

                    for i in range(0, paging):
                        try:
                            wait.until(EC.presence_of_element_located(
                                (By.XPATH, xpathTwitter.post_link())))

                            post_link = driver.find_elements(
                                "xpath", xpathTwitter.post_link())

                            for link in post_link:
                                try:
                                    topic_url.append(
                                        link.get_attribute("href"))
                                except Exception as e:
                                    print("link not have href")

                        except Exception as e:
                            pass

                        driver.execute_script(
                            "window.scrollTo(0, document.body.scrollHeight);")

                        time.sleep(2)

                    data_result = []

                    topic_url = list(set(topic_url))
                    print(f"post count: {len(topic_url)}")

                    for url in topic_url:
                        try:
                            post_result = await get_post_detail_and_comments(topic_url=url, driver=driver, keyword_check=keywords, keyword_exclude=keyword_exclude)
                            data_result.extend(post_result)
                        except Exception as e:
                            print("WARNING: get post detail and comments exception")
                            print(e)
                    try:
                        post_count = len(list(filter(
                            lambda x: x["message_type"] == "post", data_result)))
                        comment_count = len(list(filter(
                            lambda x: x["message_type"] == "comment", data_result)))

                        await fileHandle.update_log_scraping(
                            post_count=post_count,
                            comment_count=comment_count,
                            platform="twitter",
                            keyword=f"{keyword}"
                        )
                    except Exception as e:
                        print(
                            "WARNING: save log file exception [#not effect to scraping]")
                        print(e)

                    if len(data_result) > 0:
                        post_result_json = json.dumps(
                            data_result, ensure_ascii=False, indent=2).encode('utf8').decode()
                        print(post_result_json)
                        print(f"data count: {len(data_result)}")

                    try:
                        message = lineFormat.format_line_scraping_result(
                            platform="Twitter",
                            campaign_name=campaign_name,
                            keyword_name=keyword,
                            count_activity=len(data_result)
                        )

                        lineNotify.send_notify_to_dev(
                            message=message)
                    except Exception as e:
                        err_message = f"WARNING [Twitter][lineNotify.]:\n Url: {url} \n\n {e}"

                        lineNotify.send_notify_to_dev(message=err_message)

                    number_of_result += len(data_result)

                except Exception as e:
                    print(f"Post not found with keyword: {keyword}")

            print(
                f"keyword_id:{keyword_id} number_of_result:{number_of_result}")
    except Exception as e:
        print(f"WARNING: {e}.")

    driver.close()
    driver.quit()


async def get_post_detail_and_comments(topic_url="", driver=webdriver.Chrome, keyword_check=[], keyword_exclude=[]):
    print(f"{topic_url}")

    driver.get(topic_url)
    wait = WebDriverWait(driver, 10)

    data = []

    is_pass = False
    is_excluded = False

    try:
        wait.until(EC.presence_of_element_located(
            (By.XPATH, xpathTwitter.post_datetime())))

        time.sleep(3)

        content = driver.find_element(
            By.XPATH, xpathTwitter.post_detail()).get_attribute("textContent").replace("\t", "").replace("\n", "")
        like = driver.find_element(
            By.XPATH, xpathTwitter.post_like()).get_attribute("aria-label").replace(" ", "").replace(".", "").replace("Like", "").replace("like", "").replace("s", "")
        retweet = driver.find_element(
            By.XPATH, xpathTwitter.post_retweet()).get_attribute("aria-label").replace(" ", "").replace(".", "").replace("R", "").replace("r", "").replace("epost", "").replace("s", "")

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
            try:
                account_name = driver.find_element(
                    By.XPATH, xpathTwitter.post_account_name()).get_attribute("textContent")
            except Exception as e:
                account_name = "null"

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
                tweet_id = topic_url.split("/")[-1]
            except Exception as e:
                tweet_id = "null"

            data.append(twitterFormat.format_data_tweet(
                id_str=tweet_id,
                full_text=content,
                name=account_name,
                screen_name=screen_name,
                created_at=post_datetime,
                source=topic_url,
                favorite_count=like,
                retweet_count=retweet,
                message_type="post",
            ))

    except Exception as e:
        print("WARNING: get post detail")

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
                comment_is_pass = False
                comment_is_excluded = False

                try:
                    comment_tweet_link = driver.find_element(
                        By.XPATH, xpathTwitter.comment_link(only_xpath=False, length=i+1))
                    comment_content = driver.find_element(
                        By.XPATH, xpathTwitter.comment_content(only_xpath=False, length=i+1))
                    comment_account_name = driver.find_element(
                        By.XPATH, xpathTwitter.comment_account_name(only_xpath=False, length=i+1))
                    comment_screen_name = driver.find_element(
                        By.XPATH, xpathTwitter.comment_screen_name(only_xpath=False, length=i+1))
                    comment_datetime = driver.find_element(
                        By.XPATH, xpathTwitter.comment_datetime(only_xpath=False, length=i+1))
                    comment_like = driver.find_element(
                        By.XPATH, xpathTwitter.comment_like(only_xpath=False, length=i+1))
                    comment_retweet = driver.find_element(
                        By.XPATH, xpathTwitter.comment_retweet(only_xpath=False, length=i+1))
                except Exception as e:
                    # print(f"WARNING: comment no.{i+1} is Ad.")
                    continue

                try:
                    # handle case user profile is icon/image
                    try:
                        comment_account_name = comment_account_name.get_attribute(
                            "textContent").replace("\t", "").replace("\n", "")
                    except Exception as e:
                        comment_account_name = "null"

                    try:
                        comment_screen_name = comment_screen_name.get_attribute(
                            "textContent").replace("\t", "").replace("\n", "").replace("@", "")
                    except Exception as e:
                        comment_screen_name = "null"

                    # convert datetime format to MM/dd/yyyy HH:mm:ss
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
                            comment_url = comment_tweet_link.get_attribute(
                                "href")
                        except Exception as e:
                            comment_url = "null"

                        try:
                            tweet_id = comment_url.split("/")[-1]
                        except Exception as e:
                            tweet_id = "null"

                        data.append(twitterFormat.format_data_tweet(
                            id_str=tweet_id,
                            full_text=full_text,
                            name=comment_account_name,
                            screen_name=comment_screen_name,
                            created_at=comment_datetime,
                            source=comment_url,
                            favorite_count=comment_like,
                            retweet_count=comment_retweet,
                            message_type="comment",
                        ))

                except Exception as e:
                    print("WARNING: get comment detail")
                    print(e)

        except Exception as e:
            print("post no comment")

    print(f"activity count: {len(data)}")

    return data


async def login(driver=webdriver.Chrome, wait=WebDriverWait):
    print("Clearing Windows...")

    time.sleep(1)

    try:
        print("check next button")
        wait.until(EC.presence_of_element_located(
            (By.XPATH, xpathTwitter.next_button())))
    except Exception as e:
        print("WARNING: next_button not found")
        pass

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

    print(f"username: {username}")
    print(f"password: {password}")

    print("check user input")
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


async def get_post_detail_from_api(topic_url="", keyword_check=[], keyword_exclude=[]):
    data_return = None

    try:
        data_result = twitterHelper.get_tweet_data_api(url=topic_url)

        if data_result is not None:
            twitter_data = twitterFormat.format_data_fx_tweet(
                data=data_result
            )

            data_return = twitter_data

    except Exception as e:
        print(f"WARNING: get_post_detail_from_api: {e}")

    return data_return


async def run_one_post_test():
    def create_my_driver(index=0):
        try:
            time.sleep(3)

            if index > 800:
                return None

            chrome_options = webdriver.ChromeOptions()
            # chrome_options.add_argument("--incognito")
            # chrome_options.add_argument("--headless")
            # chrome_options.add_argument("--no-sandbox")
            # chrome_options.add_argument("--disable-dev-shm-usage")
            # chrome_options.add_argument("--disable-application-cache")

            my_driver = webdriver.Chrome(options=chrome_options)

            my_dict = {}
            my_dict["driver"] = my_driver
            my_dict["index"] = index

            return my_dict
        except Exception as e:
            return create_my_driver(index=index+1)

    result_create_driver = create_my_driver()

    # twitter_driver = result_create_driver['driver']
    # twitter_wait = WebDriverWait(twitter_driver, 10)

    driver = driverInstant.create_driver()
    driver.get("https://x.com/i/flow/login")
    wait = WebDriverWait(driver, 30)

    await login(driver=driver, wait=wait)

    time.sleep(3)

    topic_url = "https://x.com/godmitzu/status/1903092101648134615"
    # topic_url = "https://x.com/Skyboyz15/status/1898961977197863166"
    driver.get(topic_url)

    data = []

    time.sleep(3)

    wait.until(EC.presence_of_element_located(
        (By.XPATH, xpathTwitter.post_datetime())))

    content = driver.find_element(
        By.XPATH, xpathTwitter.post_detail()).get_attribute("textContent").replace("\t", "").replace("\n", "")
    like = driver.find_element(
        By.XPATH, xpathTwitter.post_like()).get_attribute("aria-label").replace(" ", "").replace(".", "").replace("Like", "").replace("like", "").replace("s", "")
    retweet = driver.find_element(
        By.XPATH, xpathTwitter.post_retweet()).get_attribute("aria-label").replace(" ", "").replace(".", "").replace("R", "").replace("r", "").replace("epost", "").replace("s", "")

    try:
        account_name = driver.find_element(
            By.XPATH, xpathTwitter.post_account_name()).get_attribute("textContent")
    except Exception as e:
        account_name = "null"

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
        tweet_id = topic_url.split("/")[-1]
    except Exception as e:
        tweet_id = "null"

    try:
        post_images_ele = driver.find_elements(
            By.XPATH, xpathTwitter.post_detail_image())
    except Exception as e:
        post_images_ele = []

    content_images = []
    for image in post_images_ele:
        try:
            content_images.append(image.get_attribute("src"))
        except Exception as e:
            pass

    try:
        reply_count = driver.find_element(
            By.XPATH, xpathTwitter.post_reply_count()).get_attribute("aria-label").replace(" ", "").replace(".", "").replace("replies", "").replace("Replies", "").replace('Reply', "").replace('reply', "").replace("s", "")
    except Exception as e:
        print("WARNING: get reply count")
        reply_count = 0

    try:
        bookmark_count = driver.find_element(
            By.XPATH, xpathTwitter.post_bookmark_count()).get_attribute("aria-label").replace(" ", "").replace(".", "").replace("Bookmark", "").replace("bookmark", "").replace('s', "")
    except Exception as e:
        print("WARNING: get bookmark count")
        bookmark_count = 0

    try:
        view_count = driver.find_element(
            By.XPATH, xpathTwitter.post_view())
        view_count = numberHelper.denumerize(view_count.text)
    except Exception as e:
        view_count = 0

    data.append(twitterFormat.format_data_for_mysql(
        keyword_id=1,
        tweet_id=tweet_id,
        ref_id=None,
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
    #     bookmark_count=bookmark_count,
    #     reply_count=reply_count,
    #     view_count=view_count
    # ))

    wait.until(EC.presence_of_element_located(
        (By.XPATH, xpathTwitter.comment_box_content())))

    driver.execute_script(
        "window.scrollTo(0, 3400);")
    time.sleep(3)

    comments_boxs = driver.find_elements(
        By.XPATH, xpathTwitter.comment_box_content())

    for i in range(0, len(comments_boxs)):
        try:
            # handle case user profile is icon/image
            # try:
            #     comment_account_name = driver.find_element(
            #         By.XPATH,
            #         xpathTwitter.comment_account_name(
            #             only_xpath=False, length=i+1
            #         )
            #     ).get_attribute("textContent").replace("\t", "").replace("\n", "")
            # except Exception as e:
            #     comment_account_name = "null"

            try:
                comment_account_profile_img = driver.find_element(
                    By.XPATH,
                    xpathTwitter.comment_account_profile_img(
                        only_xpath=False,
                        length=i+1
                    )
                ).get_attribute("src")
            except Exception as e:
                comment_account_profile_img = "null"

            try:
                comment_screen_name = driver.find_element(
                    By.XPATH,
                    xpathTwitter.comment_screen_name(
                        only_xpath=False,
                        length=i+1
                    )
                ).get_attribute("textContent").replace("\t", "").replace("\n", "").replace("@", "")
            except Exception as e:
                comment_screen_name = "null"

            try:
                comment_datetime = driver.find_element(
                    By.XPATH,
                    xpathTwitter.comment_datetime(
                        only_xpath=False,
                        length=i+1
                    )
                ).get_attribute("datetime").replace("\t", "").replace("\n", "")

                temp_comment_datetime = datetime.strptime(
                    comment_datetime, "%Y-%m-%dT%H:%M:%S.%fZ") + timedelta(hours=7)

                comment_datetime = temp_comment_datetime.strftime(
                    "%a %b %d %H:%M:%S +0000 %Y")

            except Exception as e:
                comment_datetime = "null"

            try:
                full_text = driver.find_element(
                    By.XPATH,
                    xpathTwitter.comment_content(
                        only_xpath=False,
                        length=i+1
                    )
                ).get_attribute("textContent").replace("\t", "").replace("\n", "")
            except Exception as e:
                full_text = "null"

            try:
                comment_like = driver.find_element(
                    By.XPATH,
                    xpathTwitter.comment_like(
                        only_xpath=False,
                        length=i+1
                    )
                ).get_attribute("textContent").replace("\t", "").replace("\n", "")

                comment_like = int(comment_like)
            except Exception as e:
                comment_like = 0

            try:
                comment_retweet = driver.find_element(
                    By.XPATH,
                    xpathTwitter.comment_retweet(
                        only_xpath=False,
                        length=i+1
                    )
                ).get_attribute("textContent").replace("\t", "").replace("\n", "")

                comment_retweet = int(comment_retweet)
            except Exception as e:
                comment_retweet = 0

            try:
                comment_reply = int(driver.find_element(
                    By.XPATH, xpathTwitter.comment_reply(only_xpath=False, length=i+1)).get_attribute(
                    "aria-label").replace("Replie", "").replace("Reply", "").replace("replies", "").replace("reply", "").replace(" ", "").replace(".", "").replace("s", "").replace("\t", "").replace("\n", ""))
            except Exception as e:
                comment_reply = 0

            try:
                comment_view = int(driver.find_element(
                    By.XPATH, xpathTwitter.comment_view(only_xpath=False, length=i+1)).get_attribute(
                    "aria-label").replace("views", "").replace("View", "").replace("post", "").replace("analytics", "").replace(" ", "").replace(".", "").replace("\t", "").replace("\n", ""))
            except Exception as e:
                comment_view = 0

            try:
                comment_url = driver.find_element(
                    By.XPATH,
                    xpathTwitter.comment_link(
                        only_xpath=False,
                        length=i+1
                    )
                ).get_attribute("href")
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
                    comment_images.append(image.get_attribute("src"))
                except Exception as e:
                    pass

            data.append(twitterFormat.format_data_for_mysql(
                keyword_id=2,
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
            #     id_str=comment_tweet_id,
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
            #     bookmark_count=0,
            #     reply_count=comment_reply,
            #     view_count=comment_view
            # ))

        except Exception as e:
            print("WARNING: get comment detail")

    print(len(data))
    # await transactionService.insert_post_and_comments_data_to_mysql(new_data=data)
