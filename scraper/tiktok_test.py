from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


from datetime import datetime
from TikTokApi import TikTokApi
from services import transaction as transaction_service

import os
import json
import time
import envconstant.env as env
import formatters.tiktok_format as tiktokFormatter
import modules.segmentation as segmentation
import xpath.tikTok as xpathTikTok
import helpers.webdriver_helper as webdriverHelper


async def scraping_data(search_data=[], count_video=30, count_comment=30):
    try:
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

                err_message = f"WARNING [tiktok API]:\n int(transaction_limit) \n\n {e}"
                print(err_message)

            try:
                transaction_remaining = int(transaction_remaining)
            except Exception as e:
                transaction_remaining = -1

                err_message = f"WARNING [tiktok API]:\n int(transaction_remaining) \n\n {e}"
                print(err_message)

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
            keyword_check = keywords

            ms_token = env.TIKTOK_MS_TOKEN

            for keyword in keywords:

                try:
                    print("Waiting for videos...")

                    data_result = await get_videos_and_comments(
                        keyword=keyword,
                        keyword_check=keyword_check,
                        keyword_exclude=keyword_exclude,
                        count_video=count_video,
                        count_comment=count_comment,
                        ms_token=ms_token
                    )

                    # todo: insert to database
                    if len(data_result) > 0:
                        try:
                            post_result_json = json.dumps(
                                data_result, ensure_ascii=False, indent=2).encode('utf8').decode()
                            print(post_result_json)
                            print(f"data count: {len(data_result)}")

                        except Exception as e:
                            err_message = f"WARNING [tiktokService.updatePostsAndCommentsData]:\n keyword: {keyword} \n\n {e}"
                            print(err_message)

                    number_of_result += len(data_result)
                except Exception as e:
                    message_err = f"WARNING in async with TikTokApi():\n {e}"

                    print(message_err)

            print(
                f"keyword_id:{keyword_id} number_of_result:{number_of_result}")

    except Exception as e:
        message_err = f"WARNING In Main [TikTokApi]:\n {e}"
        print(message_err)


async def get_videos_and_comments(keyword="", keyword_check=[], keyword_exclude=[], ms_token="", count_video=30, count_comment=30):
    print("call get_videos_and_comments")
    data_result = []
    async with TikTokApi() as api:
        print("create session")
        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3, browser="chromium", headless=True)
        try:
            tag = api.hashtag(name=keyword)
        except Exception as e:
            tag = api.hashtag(name=keyword.split(" ")[0])

        print("call tag.videos")
        async for video in tag.videos(count=count_video):
            print("call video")
            print(video.as_dict)
            video_formatted = tiktokFormatter.format_data_video(
                video.as_dict)

            is_excluded = False
            is_pass = True

            content = video_formatted["full_text"]

            # เมื่อมีคำใดคำหนึ่งใน keyword exclude อยู่ใน content หรือ title จะไม่เก็บข้อมูล
            if len(keyword_exclude) > 0:
                print("call keyword_exclude: ", keyword_exclude)
                is_excluded = any((keyword_not in content)
                                  for keyword_not in keyword_exclude)

            if len(keyword_check) > 0:
                is_pass = all(segmentation.compare_text_segmenting_all(
                    text=content, keyword=keyword) for keyword in keyword_check)
                print("call keyword_check: ", is_pass)

            if content == "" or content == " " or content == None:
                print("content is empty")
                is_pass = False

            print((not is_excluded) and is_pass)

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
                            print("comment text: ", full_text)

                        if full_text == "" or full_text == " " or full_text == None:
                            comment_is_pass = False

                        if (not comment_is_excluded) and comment_is_pass:
                            data_result.append(
                                comment_formatted)
                    except Exception as e:
                        message_err = f"WARNING in async for comment in video:\n {e}"

                        print(message_err)

    return data_result


async def get_videos_and_comments_by_url(urls=[], keyword__id="", keyword_check=[], keyword_exclude=[], ms_token="", count_video=30, count_comment=30):
    print("call get_videos_and_comments_by_url")
    data_result = []

    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3, browser="chromium", headless=True)
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
                        keyword_id=1,
                        id_str=video_formatted.get("id_str") or "",
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

                    print("before async for comment in video")
                    async for comment in video.comments(count=count_comment):
                        print("comment")
                        try:
                            comment_formatted = tiktokFormatter.format_data_video_comment(
                                comment.as_dict)

                            data_result.append(
                                tiktokFormatter.format_data_for_mysql(
                                    keyword_id=1,
                                    id_str=comment_formatted.get(
                                        "id_str") or "",
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
                            pass
            except Exception as e:
                print("Error in video info\n\n{e}")
                pass

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
        print(e)
        result = get_link_video_by_keyword(driver, wait, index, keyword)

        return result


async def run_one_post_test():

    try:
        ms_token = env.TIKTOK_MS_TOKEN

        # TODO: test by keyword
        # data_result = await get_videos_and_comments(
        #     keyword="ก้าวไกล",
        #     keyword_check=["ก้าวไกล"],
        #     keyword_exclude=[],
        #     count_video=1,
        #     count_comment=1,
        #     ms_token=ms_token
        # )

        tiktok_driver = webdriverHelper.get_webdriver()
        tiktok_wait = WebDriverWait(tiktok_driver, 10)
        data_result = get_link_video_by_keyword(
            driver=tiktok_driver,
            wait=tiktok_wait,
            index=0,
            keyword="การเมือง"
        )

        print(data_result)

        # TODO: test by url
        video_comment = await get_videos_and_comments_by_url(
            urls=data_result,
            # urls=["https://www.tiktok.com/@tom.huahin/video/7371317987426487560"],
            keyword_check=[],
            keyword_exclude=[],
            count_video=1,
            count_comment=1,
            ms_token=ms_token
        )

        print(video_comment)

        # await transaction_service.insert_post_and_comments_data_to_mysql(new_data=data_result)
        # print(data_result)
    except Exception as e:
        message_err = f"WARNING in run_one_post_test():\n {e}"

        print(message_err)
