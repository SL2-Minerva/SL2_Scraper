from datetime import datetime

import scraper.formatters.mysql_format as mysql_format
import scraper.services.transaction as transaction


def format_data_for_mysql(
    keyword_id="",
    id_str="",
    ref_id=None,
    full_text="",
    source="",
    account_name="",
    post_date="",
    content_images=[],
    profile_image=None,
    comment_count=0,
    like=0,
    view=0,
    shares=0,
    repost_count=0,
    bookmark_count=0,
    message_type="Post"
):
    post_date = datetime.strptime(post_date, "%m/%d/%Y %H:%M:%S")
    post_date = post_date.strftime("%Y-%m-%d %H:%M:%S")

    return mysql_format.format_value_mysql(
        message_id=id_str,
        reference_message_id=ref_id,
        keyword_id=keyword_id,
        message_datetime=post_date,
        author=account_name,
        source_id=transaction.source_id_tiktok,
        full_message=full_text,
        link_message=source,
        link_image=content_images[0] if len(content_images) > 0 else None,
        link_profile_image=profile_image,
        message_type=message_type,
        media_type=transaction.media_type_video,
        number_of_shares=shares,
        number_of_comments=comment_count,
        number_of_reactions=like+repost_count+bookmark_count,
        number_of_views=view,
    )


def format_data_video(data):
    post_date = int(data['createTime'])

    # MM/DD/YYYY HH:MM:SS
    post_date = datetime.fromtimestamp(post_date).strftime("%m/%d/%Y %H:%M:%S")
    now_date = datetime.now().strftime("%m/%d/%Y %H:%M:%S")

    video_link = f"https://www.tiktok.com/@{data['author']['uniqueId']}/video/{data['id']}"

    try:
        profile_image = data['author']['avatarThumb']
    except Exception as e:
        profile_image = "null"

    return {
        'id_str': data['id'],
        'video_id': data['id'],
        'message_type': "post",
        'full_text': data['desc'],
        'created_at': post_date,
        'post_date': post_date,
        'content_images': [data['video']['cover']],
        'account_name': data['author']['nickname'],
        'profile_image': profile_image,
        'source': video_link,
        'like': int(data['statsV2']['diggCount']),
        'view': int(data['statsV2']['playCount']),
        'shares': int(data['statsV2']['shareCount']),
        'comment_count': int(data['statsV2']['commentCount']),
        'repost_count': int(data['statsV2']['repostCount']),
        'bookmark_count': int(data['statsV2']['collectCount']),
        'scraping_at': now_date,
    }
    # 'comment_count': data['stats']['commentCount'],


def format_data_video_by_video_info(data):
    post_date = int(data['createTime'])

    # MM/DD/YYYY HH:MM:SS
    post_date = datetime.fromtimestamp(post_date).strftime("%m/%d/%Y %H:%M:%S")
    now_date = datetime.now().strftime("%m/%d/%Y %H:%M:%S")

    video_link = f"https://www.tiktok.com/@{data['author']['uniqueId']}/video/{data['id']}"

    try:
        profile_image = data['author']['avatarThumb']
    except Exception as e:
        profile_image = "null"

    return {
        'id_str': data['id'],
        'video_id': data['id'],
        'message_type': "post",
        'full_text': data['desc'],
        'created_at': post_date,
        'post_date': post_date,
        'content_images': [data['video']['cover']],
        'account_name': data['author']['nickname'],
        'profile_image': profile_image,
        'source': video_link,
        'like': data['stats']['diggCount'],
        'view': data['stats']['playCount'],
        'shares': data['stats']['shareCount'],
        'scraping_at': now_date,
        # 'comment_count': data['stats']['commentCount'],
    }


def format_data_video_comment(data):
    post_date = int(data['create_time'])

    # MM/DD/YYYY HH:MM:SS
    post_date = datetime.fromtimestamp(post_date).strftime("%m/%d/%Y %H:%M:%S")
    now_date = datetime.now().strftime("%m/%d/%Y %H:%M:%S")

    try:
        profile_image = data['user']['avatar_thumb']['url_list'][0]
    except Exception as e:
        profile_image = "null"

    return {
        'id_str': data['cid'],
        'comment_id': data['cid'],
        'message_type': "comment",
        'full_text': data['text'],
        'created_at': post_date,
        'post_date': post_date,
        'content_images': [],
        'account_name': data['user']['nickname'],
        'profile_image': profile_image,
        'source': data['share_info']['url'],
        'reply_comment_count': int(data['reply_comment_total']),
        'like': int(data['digg_count']),
        'view': 0,
        'shares': 0,
        'scraping_at': now_date,
    }
