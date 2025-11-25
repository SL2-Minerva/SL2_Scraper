from datetime import datetime, timedelta, timezone
from modules import telegram_notify
from helpers import twitter as twitter_helper

import formatters.mysql_format as mysql_format
import services.transaction as transaction


def format_data_for_mysql(
    keyword_id="",
    tweet_id="",
    ref_id="",
    full_text="",
    topic_url="",
    screen_name="",
    post_datetime="",
    content_images=[],
    content_videos=[],
    profile_image=None,
    retweet_count=0,
    favorite_count=0,
    reply_count=0,
    bookmark_count=0,
    view_count=0,
    message_type="Post"
):
    post_datetime = datetime.strptime(
        post_datetime, "%a %b %d %H:%M:%S +0000 %Y").astimezone(timezone.utc) + timedelta(hours=14)
    post_datetime = post_datetime.strftime("%Y-%m-%d %H:%M:%S")

    return mysql_format.format_value_mysql(
        message_id=tweet_id,
        reference_message_id=ref_id or "",
        keyword_id=keyword_id,
        message_datetime=post_datetime,
        author=screen_name,
        source_id=transaction.source_id_twitter,
        full_message=full_text,
        link_message=topic_url,
        link_image=",".join(map(str, content_images)) if len(
            content_images) > 0 else None,
        link_video=",".join(map(str, content_videos)) if len(
            content_videos) > 0 else None,
        link_profile_image=profile_image,
        message_type=message_type,
        media_type=transaction.media_type_text,
        number_of_shares=retweet_count,
        number_of_comments=reply_count,
        number_of_reactions=favorite_count+bookmark_count,
        number_of_views=view_count,
    )


def format_data_tweet(
    id_str="null",
    created_at="null",
    full_text="null",
    source="null",
    name="null",
    screen_name="null",
    profile_image="null",
    retweet_count=0,
    favorite_count=0,
    message_type="null",
    content_images=[],
    reply_count=0,
    view_count=0,
    bookmark_count=0
):
    try:
        retweet_count = int(retweet_count)
    except Exception as e:
        print(f"waring retweet:{e}")
        retweet_count = 0

    try:
        favorite_count = int(favorite_count)
    except Exception as e:
        favorite_count = 0

    return {
        "id_str": f"{id_str}",
        "created_at": f"{created_at}",
        "full_text": f"{full_text}",
        "content_images": content_images,
        "source": f"{source}",
        "user": {
            "name": f"{name}",
            "screen_name": f"{screen_name}",
            "profile_image": f"{profile_image}"
        },
        "retweet_count": retweet_count,
        "reply_count": reply_count,
        "view_count": view_count,
        "bookmark_count": bookmark_count,
        "favorite_count": favorite_count,
        "retweeted_status": {
            "id_str": f"{id_str}",
            "full_text": f"{full_text}",
        },
        "message_type": f"{message_type}"
    }


def format_data_fx_tweet(data=None):
    try:
        source = data["url"]
    except Exception as e:
        source = "null"

    try:
        id_str = data["id"]
    except Exception as e:
        id_str = "null"

    try:
        full_text = data["text"]
    except Exception as e:
        full_text = "null"

    try:
        name = data["author"]["name"]
    except Exception as e:
        name = "null"

    try:
        profile_image = data["author"]["avatar_url"]
    except Exception as e:
        profile_image = "null"

    try:
        screen_name = data["author"]["screen_name"]
    except Exception as e:
        screen_name = "null"

    try:
        created_at_date = datetime.fromtimestamp(data["created_timestamp"])
        created_at = created_at_date.strftime("%a %b %d %H:%M:%S +0000 %Y")
    except Exception as e:
        created_at = "null"

    try:
        retweet_count = int(data["retweets"])
    except Exception as e:
        print(f"waring retweet:{e}")
        retweet_count = 0

    try:
        favorite_count = int(data["likes"])
    except Exception as e:
        favorite_count = 0

    try:
        reply_count = int(data["replies"])
    except Exception as e:
        reply_count = 0

    try:
        view_count = int(data["views"])
    except Exception as e:
        view_count = 0

    try:
        if data["replying_to_status"] is not None:
            message_type = "comment"
        else:
            message_type = "post"
    except Exception as e:
        message_type = "post"

    content_images = []

    try:
        for image in data["media"]["photos"]:
            content_images.append(image["url"])
    except Exception as e:
        pass

    return {
        "id_str": f"{id_str}",
        "created_at": f"{created_at}",
        "full_text": f"{full_text}",
        "content_images": content_images,
        "source": f"{source}",
        "user": {
            "name": f"{name}",
            "screen_name": f"{screen_name}",
            "profile_image": f"{profile_image}"
        },
        "retweet_count": retweet_count,
        "reply_count": reply_count,
        "view_count": view_count,
        "bookmark_count": 0,
        "favorite_count": favorite_count,
        "retweeted_status": {
            "id_str": f"{id_str}",
            "full_text": f"{full_text}",
        },
        "message_type": f"{message_type}"
    }


def format_data_tweet_from_api(data=None):
    if data is None or data.get("legacy", None) is None:
        return None

    content_images = []
    content_videos = []
    message_type = ""

    full_text = data.get("legacy", {}).get("full_text", "")

    # TODO: Remove t.co link at the end of the tweet text
    full_text = twitter_helper.remove_tco_link_at_end(full_text)

    rest_id = data.get("rest_id", "")
    conversation_id = data.get("legacy", {}).get(
        "conversation_id_str", None)

    ref_id = data.get("legacy", {}).get("in_reply_to_status_id_str", None)
    medias = data.get("legacy", {}).get(
        "extended_entities", {}).get("media", [])

    if ref_id is None:
        message_type = "Post"

    elif ref_id == conversation_id:
        message_type = "Comment"

    elif ref_id != conversation_id:
        message_type = "Reply Comment"

    if len(medias) > 0:
        for media in medias:
            if media.get("type") == "photo" or media.get("type") == "animated_gif":
                content_images.append(media.get("media_url_https"))

            elif media.get("type") == "video":
                temp_url_video = media.get("video_info", {}).get(
                    "variants", [{}])[-1].get("url", None)

                if temp_url_video:
                    content_videos.append(temp_url_video)

    full_text_clone = str(full_text).split()

    if not full_text_clone and len(content_images) > 0:
        full_text = ",".join(map(str, content_images))

    try:
        return {
            "tweet_id": rest_id,
            "ref_id": ref_id or "",
            "full_text": full_text,
            "topic_url": f"https://x.com/a/status/{rest_id}",
            "screen_name": data["core"]["user_results"]["result"]["legacy"]["screen_name"],
            "post_datetime": data["legacy"]["created_at"],
            "content_images": content_images,
            "content_videos": content_videos,
            "profile_image": data["core"]["user_results"]["result"]["legacy"]["profile_image_url_https"],
            "retweet_count": int(data["legacy"].get("retweet_count", 0)),
            "favorite_count": int(data["legacy"].get("favorite_count", 0)),
            "reply_count": int(data["legacy"].get("reply_count", 0)),
            "bookmark_count": int(data["legacy"].get("bookmark_count", 0)),
            "view_count": int(data.get("views", {}).get("count", 0)),
            "message_type": message_type,
        }
    except Exception as e:
        telegram_notify.send_to_x_private(
            f"error [scraper][twitter_format] in format_data_tweet_from_api:\n {e}\n")
        return None
