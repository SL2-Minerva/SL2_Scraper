from datetime import datetime
from bs4 import BeautifulSoup

import formatters.mysql_format as mysql_format
import services.transaction as transaction
# *** Example of post data ***
# {
#          "id":"42893531",
#          "created_time":"1723185369",
#          "rooms":[
#             "ราชดำเนิน"
#          ],
#          "url":"https://pantip.com/topic/42893531",
#          "title":"เหตุการณ์การยุบพรรค{{em}}ก้าวไกล{{eem}}",
#          "detail":"ถ้าคุณสนใจในเหตุการณ์การยุบพรรค{{em}}ก้าวไกล{{eem}}และต้องการเข้าใจเบื้องหลังของเรื่องราวนี้มากขึ้น ผมขอชวนให้คุณดูคลิปวิดีโอที่เราได้จัดทำขึ้นครับ ในคลิปนี้ คุณจะได้เห็นรายละเอียดเพิ่มเติมเกี่ยวกับสถานการณ์ ความรู้สึกของสมาชิกพรรค และบทเรียนที่สามารถนำไปใช้ในอนาคต",
#          "comment":" จะถล่มทลายหรือเปล่าไม่รู้รู้แต่ว่าผมเชียร์พวกคุณอยู่ .. \"{{em}}ก้าวไกล{{eem}}ทำได้ดีกว่าอนาคตใหม่ แต่พรรคใหม่ต้องทำให้ดีกว่า{{em}}ก้าวไกล{{eem}}\" \"พรรคมวลชนที่เข้มแข็งคืออาวุธเดียวที่ประชาชนมีในการสร้างการเปลี่ยนแปลง เส้นขอบฟ้าทางการเมืองของเรา คือการเลือกตั้ง 2570",
#          "comment_reply":2,
#          "comment_url":"https://pantip.com/topic/42893531/comment2",
#          "author_name":"สมาชิกหมายเลข 1302781",
#          "author_url":"https://pantip.com/profile/1302781",
#          "total_comment":3,
#          "tags":[

#          ],
#          "cover_img":"None"
# }


def format_data_for_mysql(
    keyword_id="",
    topic_id="",
    ref_id="",
    title=None,
    content="",
    topic_url="",
    account_name="",
    post_date="",
    content_images=[],
    content_videos=[],
    profile_image=None,
    comment_count=0,
    sum=0,
    message_type="Post"
):
    post_date = datetime.strptime(post_date, "%m/%d/%Y %H:%M:%S")
    post_date = post_date.strftime("%Y-%m-%d %H:%M:%S")

    full_message = ""

    if title is not None:
        full_message = f"{title} {content}"
    else:
        full_message = content

    return mysql_format.format_value_mysql(
        message_id=topic_id,
        reference_message_id=ref_id,
        keyword_id=keyword_id,
        message_datetime=post_date,
        author=account_name,
        source_id=transaction.source_id_pantip,
        full_message=full_message,
        link_message=topic_url,
        link_image=",".join(map(str, content_images)) if len(
            content_images) > 0 else None,
        link_video=",".join(map(str, content_videos)) if len(
            content_videos) > 0 else None,
        link_profile_image=profile_image,
        message_type=message_type,
        media_type=transaction.media_type_text,
        number_of_shares=0,
        number_of_comments=comment_count,
        number_of_reactions=sum,
        number_of_views=0,
    )


def format_data_post_http_request(
    topic_id=None,
    title="",
    content="",
    topic_url="",
    account_name="",
    post_date="",
    content_images=[],
    content_videos=[],
    profile_image=None,
    comment_count=0,
    sum=0,
    like=0,
    laugh=0,
    love=0,
    impress=0,
    scary=0,
    surprised=0,
):
    return {
        "id": topic_id,
        "title": f"{title}",
        "full_text": f"{content}",
        "url":  f"{topic_url}",
        "message_type": "post",
        "author":  f"{account_name}",
        "post_date":  f"{post_date}",
        "content_images": content_images,
        "content_videos": content_videos,
        "profile_image": profile_image,
        "comment_count": int(comment_count),
        "sum": int(sum),
        "like": int(like),
        "laugh": int(laugh),
        "love": int(love),
        "impress": int(impress),
        "scary": int(scary),
        "surprised": int(surprised),
    }


def format_data_post_api(data={}, type="post"):
    # MM/DD/YYYY HH:MM:SS
    post_date = datetime.fromtimestamp(
        int(data['created_time'])).strftime("%m/%d/%Y %H:%M:%S")

    content_images = []
    like = 0

    try:
        title = data['title'].replace("{{em}}", "").replace("{{eem}}", "")
    except Exception as e:
        title = "null"

    try:
        content = data['detail'].replace("{{em}}", "").replace("{{eem}}", "")
    except Exception as e:
        content = "null"

    try:
        topic_url = data['url']
    except Exception as e:
        topic_url = "null"

    try:
        account_name = data['author_name']
    except Exception as e:
        account_name = "null"

    try:
        if data['cover_img'] != "None" and data['cover_img'] != None:
            content_images.append(data['cover_img'])
    except Exception as e:
        pass

    try:
        comment_count = data['total_comment']
    except Exception as e:
        comment_count = 0

    return {
        "title":  f"{title}",
        "full_text":  f"{content}",
        "content_images": content_images,
        "url":  f"{topic_url}",
        "message_type": "post",
        "author":  f"{account_name}",
        "post_date":  f"{post_date}",
        "comment_count": comment_count,
        "like": like,
    }


def format_data_post_more_detail(
    oldData={},
        sum=0,
        like=0,
        laugh=0,
        love=0,
        impress=0,
        scary=0,
        surprised=0,
        content_images=[]
):
    return {
        **oldData,
        "sum": sum,
        "like": like,
        "laugh": laugh,
        "love": love,
        "impress": impress,
        "scary": scary,
        "surprised": surprised,
        "content_images": content_images
    }


def format_data_comment_api(data, topic_url="", topic_id=""):
    content_images = []
    content_videos = []

    full_text_html_dom = BeautifulSoup(data['message'], 'html.parser')

    try:
        comment_url = f"{topic_url}/comment{data['comment_no']}"
    except Exception as e:
        comment_url = topic_url

    try:
        full_text = full_text_html_dom.get_text().replace(
            "\n", "").replace("\r", "").replace("\xa0", " ")
    except Exception as e:
        full_text = ""

    try:
        img_tags = full_text_html_dom.find_all('img')

        content_images = [img['src'] for img in img_tags]
    except Exception as e:
        content_images = []

    try:
        video_tags = full_text_html_dom.find_all('a', {'class': 'video_id'})

        content_videos = [vid['href'] for vid in video_tags]
    except Exception as e:
        content_videos = []

    try:
        comment_account_name = data['user']['name']
    except Exception as e:
        comment_account_name = "null"

    try:
        comment_profile_image = data['user']['avatar']['original']
    except Exception as e:
        comment_profile_image = None

    try:
        reply_comment_count = data['reply_count']
    except Exception as e:
        reply_comment_count = 0

    try:
        comment_like = data['emotion']['sum']
    except Exception as e:
        comment_like = 0

    try:
        like = data['emotion']['like']['count']
    except Exception as e:
        like = 0

    try:
        laugh = data['emotion']['laugh']['count']
    except Exception as e:
        laugh = 0

    try:
        love = data['emotion']['love']['count']
    except Exception as e:
        love = 0

    try:
        impress = data['emotion']['impress']['count']
    except Exception as e:
        impress = 0

    try:
        scary = data['emotion']['scary']['count']
    except Exception as e:
        scary = 0

    try:
        surprised = data['emotion']['surprised']['count']
    except Exception as e:
        surprised = 0

    try:
        comments_datetime = data['data_utime']
    except Exception as e:
        comments_datetime = "null"

    clone_content_data = str(full_text).split()
    if not clone_content_data and len(content_images) > 0:
        full_text = content_images[0]

    return {
        "post_id": topic_id,
        "comment_no": data.get('comment_no') or 0,
        "full_text":  f"{full_text}",
        "message_type": "comment",
        "url": f"{comment_url}",
        "author": f"{comment_account_name}",
        "post_date": f"{comments_datetime}",
        "reply_comment_count": int(reply_comment_count),
        "sum": int(comment_like),
        "like": int(like),
        "laugh": int(laugh),
        "love": int(love),
        "impress": int(impress),
        "scary": int(scary),
        "surprised": int(surprised),
        "content_images": content_images,
        "content_videos": content_videos,
        "profile_image": comment_profile_image
    }
