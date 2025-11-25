from lxml import etree
from bs4 import BeautifulSoup
from datetime import datetime

from modules import telegram_notify

import time
import json
import requests
import modules.segmentation as segmentation
import formatters.pantip_format as PantipFormat
import xpath.pantip as PantipXpath
import services.http_request as HttpRequest

# * ================================= INFO ================================= *
#  =========> GET LINK TOPIC
# POST: https://pantip.com/api/search-service/search/getresult
# BODY: {"keyword": "ก้าวไกล", "page": 1, "rooms": [], "timebias": true}
# HEADERS: { ptauthorize: Basic dGVzdGVyOnRlc3Rlcg==}
# ============================================================================

# ==========> GET COMMENT OF POST
# POST: https://pantip.com/forum/topic/render_comments?tid=42900476&param=&type=1&time=0.2886613058841023&_=1724233026080
# POST: https://pantip.com/forum/topic/render_comments?tid=42900476&param=page2&type=1&page=2&parent=2&expand=1&time=0.20593089352061944&_=1724231925952
# HEADERS: { x-requested-with: XMLHttpRequest}
# ============================================================================

# ==========> GET POST DETAIL
# URL: https://pantip.com/topic/42900476
# Used request to get data extract from dom
# ============================================================================

# * ================================= INFO ================================= *


async def get_post_more_detail(url="", oldData={}):
    try:
        result = requests.get(url)
        html = result.content
        soup = BeautifulSoup(html, "html.parser")
        dom = etree.HTML(str(soup))

        content_images = []
        sum = 0
        like = 0
        laugh = 0
        love = 0
        impress = 0
        scary = 0
        surprised = 0

        try:
            sum = int(dom.xpath(PantipXpath.post_like())[0].text)
        except Exception as e:
            pass

        try:
            engagements = dom.xpath(PantipXpath.post_engagements())
            like = int(engagements[0].text.replace())
            laugh = int(engagements[1].text)
            love = int(engagements[2].text)
            impress = int(engagements[3].text)
            scary = int(engagements[4].text)
            surprised = int(engagements[5].text)
        except Exception as e:
            pass

        images_dom = dom.xpath(PantipXpath.post_images())

        if len(images_dom) > 0:
            content_images = [image.attrib['src'] for image in images_dom]

        return PantipFormat.format_data_post_more_detail(
            oldData=oldData,
            sum=sum,
            like=like,
            laugh=laugh,
            love=love,
            impress=impress,
            scary=scary,
            surprised=surprised,
            content_images=content_images
        )
    except Exception as e:
        telegram_notify.send_to_pantip_private(
            message=f"Error pantip_api.get_post_more_detail\n\n{url}\n\n{e}.")
        return None


async def get_posts_data(keyword="", paging=1, keyword_checks=[], keyword_excludes=[]):
    print(f"post init...")

    result = []
    url_api = "https://pantip.com/api/search-service/search/getresult"
    headers = {
        "ptauthorize": "Basic dGVzdGVyOnRlc3Rlcg=="
    }

    body = {
        "keyword": keyword,
        "page": 1,
        "rooms": [],
        "timebias": True
    }

    for i in range(1, paging+1):
        print(f"post page {i}")

        body['page'] = i

        response = requests.post(url_api, headers=headers, json=body)
        if response.status_code == 200:
            try:
                response_content = response.content
                json_text = response_content.decode('utf-8-sig')

                if response_content.startswith(b'\xef\xbb\xbf'):
                    json_text = response_content.decode('utf-8-sig')

                json_data = json.loads(json_text)

                if len(json_data["data"]) == 0:
                    continue

                for post in json_data["data"]:
                    print(f"post formatting...")
                    f_post = PantipFormat.format_data_post_api(post)

                    is_excluded = False
                    is_pass = True

                    title = f_post['title']
                    content = f_post['full_text']

                    # เมื่อมีคำใดคำหนึ่งใน keyword exclude อยู่ใน content หรือ title จะไม่เก็บข้อมูล
                    if len(keyword_excludes) > 0:
                        is_excluded = any((keyword_not in content or keyword_not in title)
                                          for keyword_not in keyword_excludes)

                    # ใน content จะต้องมีทุกคำที่ต้องการ ถึงจะนำไปเก็บข้อมูล
                    if len(keyword_checks) > 0:
                        is_pass = all((segmentation.compare_text_segmenting_all(text=content, keyword=keyword) or segmentation.compare_text_segmenting_all(text=title, keyword=keyword))
                                      for keyword in keyword_checks)

                    if content == "" or content == None:
                        is_pass = False

                    if (not is_excluded) and is_pass:
                        f_post = await get_post_more_detail(url=f_post['url'], oldData=f_post)

                        result.append(f_post)

            except Exception as e:
                telegram_notify.send_to_pantip_private(
                    message=f"error pantip_api.get_posts_data format data\n\n{keyword}\n\n{e}.")
        else:
            telegram_notify.send_to_pantip_private(
                message=f"status_code not 200 on pantip_api.get_posts_data\n\n{url_api}\n\n{e}.")
            break

    return result


async def get_comment_data_api(url="", keyword_checks=[], keyword_excludes=[]):
    print(f"comment init...")

    temp_comment_data = []

    try:
        topic_id = url.split("/")[-1]
        comment_url_api = f"https://pantip.com/forum/topic/render_comments?tid={topic_id}"
        headers = {
            "x-requested-with": "XMLHttpRequest"
        }

        response = requests.post(comment_url_api, headers=headers)
        json_text = response.content.decode('utf-8-sig')
        json_data = json.loads(json_text)
        comments = json_data['comments']

        for comment in comments:
            print(f"comment getting...")

            f_comment = PantipFormat.format_data_comment_api(
                data=comment, topic_url=url)
            is_excluded = False
            is_pass = True

            content = f_comment['full_text']

            # เมื่อมีคำใดคำหนึ่งใน keyword exclude อยู่ใน content หรือ title จะไม่เก็บข้อมูล
            if len(keyword_excludes) > 0:
                is_excluded = any((keyword_not in content)
                                  for keyword_not in keyword_excludes)

            # ใน content จะต้องมีทุกคำที่ต้องการ ถึงจะนำไปเก็บข้อมูล
            if len(keyword_checks) > 0:
                is_pass = all((segmentation.compare_text_segmenting_all(text=content, keyword=keyword))
                              for keyword in keyword_checks)

            if content == "" or content == None:
                is_pass = False

            if (not is_excluded) and is_pass:
                temp_comment_data.append(f_comment)

    except Exception as e:
        telegram_notify.send_to_pantip_private(
            message=f"error pantip_api.get_comment_data_api format data\n\n{comment_url_api}\n\n{e}.")

    return temp_comment_data


async def get_post_and_comment_data_api(keyword="", keyword_id=None, keyword_checks=[], keyword_excludes=[]):
    def get_post_detail(post_dom):
        try:
            url = ""
            topic_id = ""
            title = ""
            content = ""
            post_date = ""
            account_name = ""
            content_images = []
            content_videos = []
            profile_image = None
            comment_count = 0
            sum = 0
            like = 0
            laugh = 0
            love = 0
            impress = 0
            scary = 0
            surprised = 0

            try:
                url = post_dom.xpath(PantipXpath.post_url())[0]
                topic_id = url.split("/")[-1]

                temp_title = post_dom.xpath(PantipXpath.post_title())
                title = " ".join([text.strip().replace("\t", "").replace(
                    "\n", "").replace("\xa0", " ")
                    for text in temp_title if text.strip()])

                temp_content = post_dom.xpath(PantipXpath.post_content())
                content = " ".join([text.strip().replace("\t", "").replace(
                    "\n", "").replace("\xa0", " ")
                    for text in temp_content if text.strip()])

                post_date = post_dom.xpath(PantipXpath.post_datetime())[0]
                account_name = post_dom.xpath(
                    PantipXpath.post_account_name())[0]
            except Exception as e:
                pass

            try:
                sum = int(post_dom.xpath(PantipXpath.post_like())[0].text)
                engagements = post_dom.xpath(PantipXpath.post_engagements())
                like = int(engagements[0].text)
                laugh = int(engagements[1].text)
                love = int(engagements[2].text)
                impress = int(engagements[3].text)
                scary = int(engagements[4].text)
                surprised = int(engagements[5].text)
            except Exception as e:
                pass

            images_dom = post_dom.xpath(PantipXpath.post_images())
            if len(images_dom) > 0:
                content_images = [image.attrib['src'] for image in images_dom]

            videos_dom = post_dom.xpath(PantipXpath.post_youtube_videos())
            if len(videos_dom) > 0:
                content_videos = [video.attrib['href'] for video in videos_dom]

            profile_image_dom = post_dom.xpath(
                PantipXpath.post_profile_image())
            if len(profile_image_dom) > 0:
                profile_image = profile_image_dom[0] or None

            content_clone_data = str(content).split()

            if not content_clone_data and len(content_images) > 0:
                content = ",".join(map(str, content_images))

            return PantipFormat.format_data_post_http_request(
                topic_id=topic_id,
                account_name=account_name,
                title=title,
                content=content,
                post_date=post_date,
                topic_url=url,
                content_images=content_images,
                content_videos=content_videos,
                profile_image=profile_image,
                comment_count=comment_count,
                sum=sum,
                like=like,
                laugh=laugh,
                love=love,
                scary=scary,
                impress=impress,
                surprised=surprised
            )
        except Exception as e:
            telegram_notify.send_to_pantip_private(
                message=f"error pantip_api.get_post_detail\n\n{e}.")
            return None

    if (keyword_id == None):
        return []

    posts_and_comment_data = []

    try:
        print(f"post init...")
        smart_search_dom = HttpRequest.get_pantip_smart_search_dom(
            keyword=keyword, paging=1)

        suffix_urls = smart_search_dom.xpath(
            PantipXpath.post_list_from_smart_search())

        for s_url in suffix_urls:
            print(f"post getting...")
            post_url = f"https://search.pantip.com{s_url}"

            post_dom = HttpRequest.get_dom_by_url(post_url)
            f_post = get_post_detail(post_dom)

            if f_post == None:
                continue

            now_datetime = datetime.now()
            post_datetime = datetime.strptime(
                f_post['post_date'], "%m/%d/%Y %H:%M:%S")

            diff_time = now_datetime - post_datetime
            if diff_time.days > 1:
                continue

            is_excluded = False
            is_pass = True

            title = f_post['title']
            content = f_post['full_text']

            # เมื่อมีคำใดคำหนึ่งใน keyword exclude อยู่ใน content หรือ title จะไม่เก็บข้อมูล
            if len(keyword_excludes) > 0:
                is_excluded = any((keyword_not in content or keyword_not in title)
                                  for keyword_not in keyword_excludes)

            # ใน content จะต้องมีทุกคำที่ต้องการ ถึงจะนำไปเก็บข้อมูล
            if len(keyword_checks) > 0:
                is_pass = all((segmentation.compare_text_segmenting_all(text=content, keyword=keyword) or segmentation.compare_text_segmenting_all(text=title, keyword=keyword))
                              for keyword in keyword_checks)

            if content == "" or content == None:
                is_pass = False

            if (not is_excluded) and is_pass:
                topic_url = f_post['url']
                topic_id = topic_url.split("/")[-1]

                comments_response = HttpRequest.get_pantip_comments_by_topic_id(
                    topic_id=topic_id)

                f_post['comment_count'] = int(
                    comments_response.get('count') or 0)
                posts_and_comment_data.append(PantipFormat.format_data_for_mysql(
                    keyword_id=keyword_id,
                    topic_id=topic_id,
                    ref_id="",
                    title=f_post['title'],
                    content=f_post['full_text'],
                    post_date=f_post['post_date'],
                    content_images=f_post['content_images'],
                    content_videos=f_post['content_videos'],
                    profile_image=f_post['profile_image'],
                    account_name=f_post['author'],
                    topic_url=f_post['url'],
                    comment_count=f_post['comment_count'],
                    sum=f_post['sum'],
                    message_type="Post",
                ))

                comments_data = comments_response.get('comments') or []

                for comment in comments_data:
                    print(f"comment getting...")

                    f_comment = PantipFormat.format_data_comment_api(
                        data=comment, topic_url=topic_url, topic_id=topic_id)

                    is_pass_comment = True  # ของเดิมเป็น False หากเปิดใช้งานการตรวจสอบเงือนไข
                    is_excluded_comment = False

                    content = f_comment['full_text']

                    # # เมื่อมีคำใดคำหนึ่งใน keyword exclude อยู่ใน content หรือ title จะไม่เก็บข้อมูล
                    # if len(keyword_excludes) > 0:
                    #     is_excluded_comment = any((keyword_not in content)
                    #                               for keyword_not in keyword_excludes)

                    # # ใน content จะต้องมีทุกคำที่ต้องการ ถึงจะนำไปเก็บข้อมูล
                    # if len(keyword_checks) > 0:
                    #     is_pass_comment = all((segmentation.compare_text_segmenting_all(text=content, keyword=keyword))
                    #                           for keyword in keyword_checks)

                    # if content == "" or content == None:
                    #     is_pass_comment = False

                    if (not is_excluded_comment) and is_pass_comment:
                        posts_and_comment_data.append(PantipFormat.format_data_for_mysql(
                            keyword_id=keyword_id,
                            topic_id=f_comment.get('comment_no') or 0,
                            ref_id=topic_id,
                            title=None,
                            content=f_comment['full_text'],
                            post_date=f_comment['post_date'],
                            content_images=f_comment['content_images'],
                            content_videos=f_comment['content_videos'],
                            profile_image=f_comment.get(
                                'profile_image') or None,
                            account_name=f_comment['author'],
                            topic_url=f_comment['url'],
                            comment_count=f_comment['reply_comment_count'],
                            sum=f_comment['sum'],
                            message_type="Comment",
                        ))

    except Exception as e:
        telegram_notify.send_to_pantip_private(
            message=f"error pantip_api.get_post_and_comment_data_api\n\n{e}.")

    return posts_and_comment_data
