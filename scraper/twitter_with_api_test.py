
import json
import time
import random

from datetime import datetime, timedelta, timezone
from services import twitter_api
from modules import segmentation
from formatters import twitter_format
from services import transaction as transaction_service
from helpers import twitter as twitter_helper


def get_tweet_ids_by_keyword(keyword="ลิซ่า", cursor=None, keyword_exclude=[], keyword_check=[], index=1, x_client_transaction_ids=[]):
    if len(x_client_transaction_ids) <= 0:
        x_client_transaction_ids = twitter_api.x_ct_ids_search_timeline.copy()

        twitter_helper.wait_for_next_minute()

    print("getting tweet ids...")

    tweet_ids = []

    try:
        result = twitter_api.get_tweet_by_keyword(
            keyword=keyword,
            cursor=cursor,
            x_client_transaction_id=x_client_transaction_ids[0]
        )

        x_client_transaction_ids.pop(0)

        instructions = result.get("data", {}).get(
            "search_by_raw_query", {}).get("search_timeline", {}).get("timeline", {}).get("instructions", [])

        if len(instructions) == 0:
            return []

        entries = instructions[0].get("entries", [])
        if len(entries) == 0:
            return []

        for entry in entries:
            if (entry.get("content", {})
                .get("itemContent", {})
                .get("tweet_results", {})
                .get("result", {})
                    .get("legacy")):

                tweet_result = entry["content"]["itemContent"]["tweet_results"]["result"]

                created_at = tweet_result["legacy"]["created_at"]
                full_text = tweet_result["legacy"]["full_text"]
                rest_id = tweet_result["rest_id"]

                now_datetime = datetime.now(timezone.utc)
                created_at_datetime = datetime.strptime(
                    created_at, "%a %b %d %H:%M:%S %z %Y")

                diff_time = now_datetime - created_at_datetime

                if diff_time.days > 1:
                    continue

                is_excluded = False
                is_pass = True

                if len(keyword_exclude) > 0:
                    is_excluded = any((keyword_not in full_text)
                                      for keyword_not in keyword_exclude)

                if len(keyword_check) > 0:
                    is_pass = all(segmentation.compare_text_segmenting_all(
                        text=full_text, keyword=keyword) for keyword in keyword_check)

                if full_text == "" or full_text == " " or full_text == None:
                    is_pass = False

                if is_pass and not is_excluded:
                    tweet_ids.append(rest_id)

        new_cursor = entries[-1].get("content", {}).get("value", None)

        if new_cursor is None:
            new_cursor = instructions[-1].get(
                "entry", {}).get("content", {}).get("value", None)

        if new_cursor and index < 3:
            index += 1
            more_result = get_tweet_ids_by_keyword(
                keyword=keyword,
                cursor=new_cursor,
                keyword_check=keyword_check,
                keyword_exclude=keyword_exclude,
                index=index,
                x_client_transaction_ids=x_client_transaction_ids
            )

            tweet_ids.extend(more_result)
    except Exception as e:
        print(
            f"\nerror [scraper][twitter_with_api_test] in get_tweet_ids_by_keyword:\n {e}\n")

    return tweet_ids


def get_tweet_detail(tweet_id=None, cursor=None, keyword_exclude=[], keyword_check=[], x_transaction_id=""):
    new_cursor = None
    tweet_details = []

    random_second = random.randrange(1, 2)
    print("sleeping...", random_second)

    time.sleep(random_second)
    print("getting tweet detail...")

    result = twitter_api.get_tweet_detail(
        tweet_id=tweet_id, cursor=cursor, x_client_transaction_id=x_transaction_id)
    instructions = result.get("data", {}).get(
        "threaded_conversation_with_injections_v2", {}).get("instructions", [])

    if len(instructions) > 0:
        entries = []

        for instruction in instructions:
            if len(instruction.get('entries', [])) > 0:
                entries = instruction.get('entries', [])
                break

        if len(entries) > 0:

            for entry in entries:
                print("getting tweet detail...")

                tweet = entry.get("content", {}).get(
                    "itemContent", {}).get("tweet_results", {}).get("result", None)

                reply_tweet = entry.get("content", {}).get("items", [])

                if tweet is not None:
                    formatted_tweet = twitter_format.format_data_tweet_from_api(
                        data=tweet)

                    if formatted_tweet is not None:
                        tweet_details.append(formatted_tweet)

                elif len(reply_tweet) > 0:

                    for r_tweet in reply_tweet:
                        tweet = r_tweet.get("item", {}).get("itemContent", {}).get(
                            "tweet_results", {}).get("result", None)

                        if tweet is None:
                            continue

                        formatted_tweet = twitter_format.format_data_tweet_from_api(
                            data=tweet)

                        if formatted_tweet is None:
                            continue

                        message_type = formatted_tweet.get(
                            "message_type", "Post")
                        if message_type == "Post":
                            created_at = formatted_tweet.get(
                                "post_datetime", None)
                            full_text = formatted_tweet.get("full_text", None)

                            now_datetime = datetime.now(timezone.utc)
                            created_at_datetime = datetime.strptime(
                                created_at, "%a %b %d %H:%M:%S %z %Y")

                            diff_time = now_datetime - created_at_datetime

                            if diff_time.days > 1:
                                continue

                            is_excluded = False
                            is_pass = True

                            if len(keyword_exclude) > 0:
                                is_excluded = any((keyword_not in full_text)
                                                  for keyword_not in keyword_exclude)

                            if len(keyword_check) > 0:
                                is_pass = all(segmentation.compare_text_segmenting_all(
                                    text=full_text, keyword=keyword) for keyword in keyword_check)

                            if full_text == "" or full_text == " " or full_text == None:
                                is_pass = False

                            if is_pass and not is_excluded:
                                tweet_details.append(formatted_tweet)
                        else:
                            tweet_details.append(formatted_tweet)

            new_cursor = entries[-1].get(
                "content", {}).get("itemContent", {}).get("value", None)

    return tweet_details, new_cursor


def get_tweet_detail_by_ids(tweet_ids=[], keyword_exclude=[], keyword_check=[]):
    if len(tweet_ids) == 0:
        return []

    summary_tweet = []
    x_transaction_ids = twitter_api.x_ct_ids_tweet_detail.copy()

    try:
        for tweet_id in tweet_ids:
            new_cursor = None

            for i in range(2):
                if len(x_transaction_ids) <= 0:
                    x_transaction_ids = twitter_api.x_ct_ids_tweet_detail.copy()

                    print("x_transaction_id is expire, 1 minute reloading...")
                    twitter_helper.wait_for_next_minute()

                tweet_detail, cursor = get_tweet_detail(
                    tweet_id=tweet_id,
                    cursor=new_cursor,
                    keyword_exclude=keyword_exclude,
                    keyword_check=keyword_check,
                    x_transaction_id=x_transaction_ids[0]
                )

                print("pop x_transaction_id:", x_transaction_ids[0])
                x_transaction_ids.pop(0)

                summary_tweet.extend(tweet_detail)

                new_cursor = cursor
                if new_cursor is None:
                    break

    except Exception as e:
        print(
            f"\nerror [scraper][twitter_with_api_test] in get_tweet_detail_by_ids:\n {e}\n")

    return summary_tweet


def format_data_mysql(keyword_id=None, data={}):

    return twitter_format.format_data_for_mysql(
        keyword_id=keyword_id,
        tweet_id=data.get("tweet_id", ""),
        ref_id=data.get("ref_id", ""),
        topic_url=data.get("topic_url", ""),
        full_text=data.get("full_text", ""),
        post_datetime=data.get("post_datetime", ""),
        content_images=data.get("content_images", []),
        profile_image=data.get("profile_image", ""),
        screen_name=data.get("screen_name", ""),
        message_type=data.get("message_type", ""),
        reply_count=data.get("reply_count", 0),
        retweet_count=data.get("retweet_count", 0),
        bookmark_count=data.get("bookmark_count", 0),
        favorite_count=data.get("favorite_count", 0),
        view_count=data.get("view_count", 0)
    )


async def run():
    try:
        print("Twitter Api is started. ")
        results = []

        # tweet_ids = get_tweet_ids_by_keyword(
        #     keyword="การเมือง",
        #     x_client_transaction_ids=twitter_api.x_ct_ids_search_timeline.copy())
        # print(tweet_ids)
        # print("tweets_detail:", len(tweet_ids))

        tweets_detail = get_tweet_detail_by_ids(
            tweet_ids=["1917502601593303150", "1917514881013801056", "1917530094236754127"])
        print(tweets_detail)
        print("tweets_detail:", len(tweets_detail))

        # tweets_detail = [format_data_mysql(
        #     keyword_id=11, data=tweet) for tweet in tweets_detail]

        # results.extend(tweets_detail)
        # print("results:", len(results))
        # print(results)

        # await transaction_service.insert_post_and_comments_data_to_mysql(new_data=results)

        # result = twitter_api.get_tweet_detail(
        #     tweet_id="1908533590482124987", cursor="bQAAAPBeHBm2-MLXycutmOY0msG7xZPno_w06Ieztcuhqvw0nIS75YSTqvw0ioO2re3Q1_o0ysa5ufbcmvw04IW69fvro_w0goGx3fyDqPw00IC0_e7yqfw0uoO00af4ofw0lMK71cjIpfw0JQISFQQAAA")
        # print(result)
    except Exception as e:
        print(f"Twitter\n\n run error\n{e}.")
