from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver

from datetime import datetime
from TikTokApi import TikTokApi
import os
import json
import time
import scraper.formatters.tiktok_format as tiktokFormatter
import scraper.modules.segmentation as segmentation
import scraper.xpath.tikTok as xpathTikTok

from helpers import webdriver_helper as webdriverHelper


async def get_videos_and_comments_by_url(urls=[], keyword__id="", keyword_check=[], keyword_exclude=[], ms_token="", count_video=30, count_comment=30):
    data_result = []

    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3)
        print("create session")

        for url in urls:
            try:
                video = api.video(
                    url=url
                )
                print("call video")
                video_info = await video.info()

                video_formatted = tiktokFormatter.format_data_video(
                    video_info)

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
                        keyword_id=1,
                        id_str=video_formatted.get("id_str") or None,
                        ref_id=None,
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
                    # data_result.append(video_formatted)

                    print("before async for comment in video")
                    async for comment in video.comments(count=count_comment):
                        print("comment")
                        try:
                            comment_formatted = tiktokFormatter.format_data_video_comment(
                                comment.as_dict)

                            print("comment_formatted")

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

                            #! bypass not in comment_is_pass for test ignore keyword_check only
                            if (not comment_is_excluded) and not comment_is_pass:
                                data_result.append(
                                    tiktokFormatter.format_data_for_mysql(
                                        keyword_id=1,
                                        id_str=comment_formatted.get(
                                            "id_str") or None,
                                        ref_id=video_formatted.get(
                                            "id_str") or None,
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
                                # data_result.append(
                                #     comment_formatted)
                        except Exception as e:
                            message_err = f"WARNING in async for comment in video:\n {e}"
                            print(message_err)

            except Exception as e:
                print(e)
                message_err = f"Tiktok\n\nWARNING in async for video in video.info():\n {e}"

                if "empty response" not in message_err and "NoneType" not in message_err:
                    print(message_err)

    return data_result


def get_link_video_by_keyword(driver, wait, index=0, keyword=""):
    if keyword == "":
        return []

    index = int(index) + 1

    if index > 30:
        return []

    try:
        links = []
        timestamp = int(datetime.now().timestamp())

        url = f"https://www.tiktok.com/search?q={keyword}&t={timestamp}"
        print(url)

        driver.get(url)
        wait.until(EC.presence_of_element_located(
            (By.XPATH, xpathTikTok.video_link())))

        links_video = driver.find_elements(
            "xpath", xpathTikTok.video_link())

        for lv in links_video:
            links.append(lv.get_attribute("href"))

        return links
    except Exception as e:
        print("re bypass captcha...")
        result = get_link_video_by_keyword(driver, wait, index, keyword)

        return result


async def run_one_post_test():
    tiktok_driver = webdriverHelper.get_webdriver()
    tiktok_wait = WebDriverWait(tiktok_driver, 10)

    try:
        ms_token = 'gPnFHZ_4mQKzTKT2zhLI2uLqGt7cCCdPIj8g1yKHgKHkJJJz4l6mdGMKbxOn4FEIPDR3NOn2nmEF68udu2zriZWbFyjSqItQWzdSLwYqiV-nREggIuLTk7k9s3bOOmiH5M47plGj5iBfpg=='

        # TODO: test by url
        # data_result = await get_videos_and_comments_by_url(
        #     urls=["https://www.tiktok.com/@tom.huahin/video/7371317987426487560"],
        #     keyword_check=[],
        #     keyword_exclude=[],
        #     count_video=1,
        #     count_comment=1,
        #     ms_token=ms_token
        # )

        data_result = get_link_video_by_keyword(
            driver=tiktok_driver,
            wait=tiktok_wait,
            index=0,
            keyword="ก้าวไกล"
        )

        print(data_result)
    except Exception as e:
        message_err = f"WARNING in run_one_post_test():\n {e}"

        print(message_err)
