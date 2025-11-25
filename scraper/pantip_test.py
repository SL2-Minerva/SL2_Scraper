
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver


import json
import time
import driver.main_test as driverInstant
import xpath.pantip as xpathPantip
import modules.segmentation as segmentation
import modules.file_handle as fileHandle
import modules.line_notify as lineNotify


async def run():
    paging = driverInstant.get_paging_from_argv()

    search_data = [{
        "keyword_id": 123,
        "campaign_id": 123,
        "campaign_name": "การเมื่อง dev",
        "keyword": ["ก้าวไกล"],
        "keyword_exclude": [],
    }]

    await scraping_data_with_keyword_and_or_not(search_data=search_data, paging=paging)


async def scraping_data_with_keyword_and_or_not(search_data=[], paging=1):
    try:
        driver = driverInstant.create_driver()

        for search in search_data:
            keyword_id = search["keyword_id"]
            campaign_id = search["campaign_id"]
            campaign_name = search["campaign_name"]

            keywords = search["keyword"]
            keyword_exclude = search["keyword_exclude"]

            number_of_result = 0

            for keyword in keywords:
                url = f"https://pantip.com/search?q={keyword}&timebias=true"

                driver.get(url)
                try:

                    wait = WebDriverWait(driver, 5)

                    print("Wait for post link...")
                    wait.until(EC.presence_of_element_located(
                        (By.XPATH, xpathPantip.post_link())))

                    # scroll to bottom
                    for i in range(0, paging):
                        print(f"Scroll to bottom: {i}")

                        driver.execute_script(
                            "window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(2)

                    topic_url = []
                    data_result = []

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
                                message=f"WARNING PANTIP for url in topic_url: {temp_url} {e}")

                    try:
                        post_count = len(list(filter(
                            lambda x: x["message_type"] == "post", data_result)))
                        comment_count = len(list(filter(
                            lambda x: x["message_type"] == "comment", data_result)))

                        await fileHandle.update_log_scraping(
                            post_count=post_count,
                            comment_count=comment_count,
                            platform="pantip",
                            keyword=f"{keyword}"
                        )
                    except Exception as e:
                        pass

                    print(f"post count: {len(topic_url)}")

                    if len(data_result) > 0:
                        post_result_json = json.dumps(
                            data_result, ensure_ascii=False, indent=2).encode('utf8').decode()
                        print(post_result_json)

                    number_of_result += len(data_result)

                except Exception as e:
                    print(f"Post not found with keyword: {keyword}")
            print(
                f"keyword_id:{keyword_id} number_of_result:{number_of_result}")
        driver.quit()
    except Exception as e:
        lineNotify.send_notify_to_dev(
            message=f"WARNING PANTIP scraping_data_with_keyword_and_or_not: {e}")


async def get_post_detail_and_comments(topic_url="", driver=webdriver.Chrome, keyword_check=[], keyword_exclude=[]):
    print(f"{topic_url}")

    driver.get(topic_url)
    wait = WebDriverWait(driver, 20)

    data = []

    is_pass = True
    is_excluded = False

    try:
        time.sleep(3)

        wait.until(EC.presence_of_element_located(
            (By.XPATH, xpathPantip.post_title())))

        title = driver.find_element(
            "xpath", xpathPantip.post_title()).get_attribute("textContent").replace("\t", "").replace("\n", "")
        content = driver.find_element(
            "xpath", xpathPantip.post_content()).get_attribute("textContent").replace("\t", "").replace("\n", "")
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

            data.append({
                "title": title,
                "full_text": content,
                "url": topic_url,
                "message_type": "post",
                "author": account_name,
                "post_date": datetime,
                "like": like,
            })
    except Exception as e:
        lineNotify.send_notify_to_dev(
            message=f"WARNING PANTIP AT find post title: {e}")

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

                    full_text = comments_content[i].get_attribute(
                        "textContent").replace("\t", "").replace("\n", "")

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
                            "full_text": full_text,
                            "message_type": "comment",
                            "url": topic_url,
                            "author": comment_account_name,
                            "post_date": post_date,
                            "like": comment_like
                        })
                except Exception as e:
                    lineNotify.send_notify_to_dev(
                        message=f"WARNING PANTIP AT for i in range(0, len(comments_content)): {e}")
        except Exception as e:
            print("Post not found comments")

    print(f"activity count: {len(data)}")

    return data


# one post test

async def run_one_post_test():
    topic_url = "https://pantip.com/topic/42212261"

    driver = driverInstant.create_driver()
    driver.get(topic_url)
    wait = WebDriverWait(driver, 20)

    data = []

    time.sleep(3)

    wait.until(EC.presence_of_element_located(
        (By.XPATH, xpathPantip.comment_box_content())))

    comments = driver.find_elements(
        By.XPATH, xpathPantip.comment_box_content())

    index = 1

    for comment in comments:

        full_text = comment.find_element(
            "xpath",
            xpathPantip.comment_content(
                only_xpath=False,
                length=index
            )
        ).get_attribute("textContent").replace("\t", "").replace("\n", "")

        images_ele = comment.find_elements(
            "xpath",
            xpathPantip.comment_images(
                only_xpath=False,
                length=index
            )
        )

        comment_account_name = comment.find_element(
            "xpath",
            xpathPantip.comment_account_name(
                only_xpath=False,
                length=index
            )
        ).get_attribute("textContent")

        comments_datetime = comment.find_element(
            "xpath",
            xpathPantip.comment_datetime(
                only_xpath=False,
                length=index
            )
        ).get_attribute("data-utime").replace("\t", "").replace("\n", "")

        comment_like = comment.find_element(
            "xpath",
            xpathPantip.comment_like(
                only_xpath=False,
                length=index
            )
        ).get_attribute("textContent").replace("\t", "").replace("\n", "")

        content_images = []

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
                            "content_images": content_images
        })

        index += 1

        if index > 9:
            break

    print(data)


async def run_link_post_test():
    paging = 2
    topic_url = []
    url = f"https://pantip.com/search?q=ก้าวไกล&timebias=true"

    driver = driverInstant.create_driver()
    driver.get(url)
    wait = WebDriverWait(driver, 20)

    time.sleep(3)
    wait.until(EC.presence_of_element_located(
        (By.XPATH, xpathPantip.post_link())))

    for i in range(0, paging):
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    post_link = driver.find_elements(
        "xpath", xpathPantip.post_link())
    for link in post_link:
        topic_url.append(link.get_attribute("href"))

    print(topic_url)
