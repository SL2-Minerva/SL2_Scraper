
import json
import time
import random

from datetime import datetime, timedelta, timezone
from services import twitter_api, keywords as keywords_service, transaction as transaction_service
from modules import segmentation, file_handle, telegram_notify
from formatters import twitter_format, data_format, line_format
from helpers import error_handle, scraper as scraper_helper, twitter as twitter_helper


def get_tweet_ids_by_keyword(keyword=None, cursor=None, keyword_exclude=[], keyword_check=[], index=1, x_transaction_ids=[], is_first_time=False):
    if keyword is None:
        return []

    if is_first_time:
        twitter_helper.wait_for_next_minute()

    new_x_transaction_ids = x_transaction_ids.copy()

    if len(new_x_transaction_ids) <= 0:
        new_x_transaction_ids = twitter_api.x_ct_ids_search_timeline.copy()

        twitter_helper.wait_for_next_minute()

    random_second = random.randrange(1, 8)
    print("sleeping...", random_second)

    time.sleep(random_second)

    print("getting tweet ids...")

    tweet_ids = []

    try:
        result = twitter_api.get_tweet_by_keyword(
            keyword=keyword,
            cursor=cursor,
            x_client_transaction_id=new_x_transaction_ids[0]
        )

        new_x_transaction_ids.pop(0)

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
                x_transaction_ids=new_x_transaction_ids,
                is_first_time=False
            )

            tweet_ids.extend(more_result)
    except Exception as e:
        print(
            f"\nerror [scraper][twitter_with_api_test] in get_tweet_ids_by_keyword:\n {e}\n")

    return tweet_ids


def get_tweet_detail(tweet_id=None, cursor=None, keyword_exclude=[], keyword_check=[], x_transaction_id=""):
    new_cursor = None
    tweet_details = []
    random_second = random.randrange(1, 8)

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
        else:
            telegram_notify.send_to_x_private(
                message=f"get_tweet_detail: no entry found.\n\n something changed in response three.")

    return tweet_details, new_cursor


def get_tweet_detail_by_ids(tweet_ids=[], keyword_exclude=[], keyword_check=[]):
    if len(tweet_ids) == 0:
        return []

    twitter_helper.wait_for_next_minute()

    summary_tweet = []
    x_transaction_ids = twitter_api.x_ct_ids_tweet_detail.copy()

    try:
        for tweet_id in tweet_ids:
            new_cursor = None

            for i in range(3):
                if len(x_transaction_ids) <= 0:
                    x_transaction_ids = twitter_api.x_ct_ids_tweet_detail.copy()
                    twitter_helper.wait_for_next_minute()

                tweet_detail, cursor = get_tweet_detail(
                    tweet_id=tweet_id,
                    cursor=new_cursor,
                    keyword_exclude=keyword_exclude,
                    keyword_check=keyword_check,
                    x_transaction_id=x_transaction_ids[0]
                )

                x_transaction_ids.pop(0)

                summary_tweet.extend(tweet_detail)

                new_cursor = cursor
                if new_cursor is None:
                    break

    except Exception as e:
        telegram_notify.send_to_private(
            message=f"error [scraper][twitter_with_api_test] in get_tweet_detail_by_ids:\n {e}\n")

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
        content_videos=data.get("content_videos", []),
        profile_image=data.get("profile_image", ""),
        screen_name=data.get("screen_name", ""),
        message_type=data.get("message_type", ""),
        reply_count=data.get("reply_count", 0),
        retweet_count=data.get("retweet_count", 0),
        bookmark_count=data.get("bookmark_count", 0),
        favorite_count=data.get("favorite_count", 0),
        view_count=data.get("view_count", 0)
    )


async def scraping_data(search_data=[]):
    campaign_lists = search_data

    total_count_result = 0

    # TODO:[START] use for debugging
    # in_range_condition_message = ""
    # transaction_limit_condition_message = ""
    # TODO:[END] use for debugging

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
        total_insert = 0
        total_update = 0

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
        if not scraper_helper.is_in_range_date(start_at=start_at, end_at=end_at):
            # temp_in_rage_condition_message = f"campaign:{campaign_name} start_at:{start_at} end_at:{end_at}\n"
            # in_range_condition_message += temp_in_rage_condition_message
            continue

        # TODO: condition 2 check limit transaction remaining
        if not scraper_helper.is_in_transaction_limit(transaction_limit=transaction_limit, transaction_remaining=transaction_remaining):
            # temp_transaction_condition_message = f"campaign:{campaign_name} limit:{transaction_limit} remaining:{transaction_remaining}\n"
            # transaction_limit_condition_message += temp_transaction_condition_message
            continue

        temp_keywords = []
        keyword_item_lists = campaign["keywords"]

        for keyword_item in keyword_item_lists:
            keyword_id = keyword_item["keyword_id"]
            keywords = keyword_item["keywords"]
            keyword_checks = keyword_item["keywords"]
            keyword_excludes = keyword_item["keyword_excludes"]
            last_craw_date = keyword_item["last_crawed_at"]

            # TODO: condition 3 check frequency
            if not scraper_helper.is_out_of_frequency(frequency_minute=frequency, last_craw_date=last_craw_date):
                continue

            await transaction_service.save_last_craw_at(
                keyword_id=keyword_id,
                source_id=transaction_service.source_id_twitter
            )

            number_of_result = 0
            flag_error = []

            for keyword in keywords:
                temp_keywords.append(f"{keyword}({keyword_id})")

                data_result = []

                tweet_ids = get_tweet_ids_by_keyword(
                    keyword=keyword,
                    keyword_check=keyword_checks,
                    keyword_exclude=keyword_excludes,
                    x_transaction_ids=twitter_api.x_ct_ids_search_timeline.copy(),
                    is_first_time=True,
                )

                tweets_detail = get_tweet_detail_by_ids(
                    tweet_ids=tweet_ids,
                    keyword_check=keyword_checks,
                    keyword_exclude=keyword_excludes
                )

                tweets_detail = [format_data_mysql(
                    keyword_id=keyword_id, data=tweet) for tweet in tweets_detail]

                data_result.extend(tweets_detail)

                try:
                    number_of_result += len(data_result)

                    # todo: insert to database
                    if len(data_result) > 0:
                        insert_len, update_len = await transaction_service.insert_post_and_comments_data_to_mysql(new_data=data_result)
                        total_insert += insert_len
                        total_update += update_len

                        # * insert to second database
                        await transaction_service.insert_post_and_comments_data_to_mysql(new_data=data_result, isSecondDB=True)
                except Exception as e:
                    # todo: =============> START: handle error <============
                    try:
                        result_message = error_handle.handle(e)

                        if result_message["is_error"]:
                            if "ส่งถึง Developer" in result_message['message']:
                                flag_error.append(
                                    "ไม่สามารถเชื่อมต่อ mongodb ได้")
                            else:
                                flag_error.append(
                                    f"{result_message['message']}")

                    except Exception as ee:
                        pass
                    # todo: =============> END: handle error <============

                time.sleep(1)

            flag_error_message = ""

            try:
                if number_of_result == 0:
                    flag_error = list(set(flag_error))
                    flag_error_message = ", ".join(flag_error)

            except Exception as e:
                pass

            await transaction_service.pushTransactionScrapingResult(
                keyword_id=keyword_id,
                source_id=transaction_service.source_id_twitter,
                number_of_result=number_of_result,
                organization_id=organization_id,
                flag_error=flag_error_message
            )

            total_result += number_of_result

        datetime_end_campaign_scraping = datetime.now()
        keyword_str = ", ".join(temp_keywords)

        # * Notify when have keyword to scraping
        if len(temp_keywords) > 0:
            try:
                line_message = line_format.format_campaign_result(
                    platform="Twitter",
                    campaign_name=campaign_name,
                    campaign_id=campaign_id,
                    keyword=keyword_str,
                    datetime_start_campaign_scraping=datetime_start_campaign_scraping,
                    datetime_end_campaign_scraping=datetime_end_campaign_scraping,
                    total_result=total_result,
                    total_insert=total_insert,
                    total_update=total_update,
                )
                telegram_notify.send_to_x_work_process(message=line_message)
            except Exception as e:
                telegram_notify.send_to_x_private(
                    message=f"Error twitter_with_api.format_campaign_result\n\n{e}")

        total_count_result += total_result

        time.sleep(1)

    # TODO:[START] use for debugging
    # if in_range_condition_message != "":
    #     telegram_notify.send_to_x_private(
    #         message=f"Twitter\n\n ไม่เข้าเงือนไขช่วงเวลา:\n{in_range_condition_message}")

    # if transaction_limit_condition_message != "":
    #     telegram_notify.send_to_x_private(
    #         message=f"Twitter\n\n ไม่เข้าเงือนไข transaction limit:\n{transaction_limit_condition_message}")
    # TODO:[END] use for debugging

    return total_count_result


async def run():
    try:
        print("Twitter scraping call to start.")
        telegram_notify.send_to_x_work_process(
            "Twitter scraping call to start.")

        while True:
            try:
                raw_data = await keywords_service.getActiveKeyword(platform=keywords_service.platform_twitter)
                search_data = []

                for data in raw_data:
                    try:
                        tempKeyword = []
                        tempKeywordExclude = []

                        if isinstance(data["name"], str) and data["name"] != "":
                            tempKeyword = data["name"].split(",")

                        if isinstance(data["keyword_exclude"], str) and data["keyword_exclude"] != "":
                            tempKeywordExclude = data["keyword_exclude"].split(
                                ",")

                        last_craw_date = None

                        if data["id"] != None:
                            last_craw_date = await keywords_service.get_last_craw_date(keyword_id=data["id"], source_id=transaction_service.source_id_twitter)

                        search_data.append({
                            "keyword_id": data["id"],
                            "campaign_id": data["campaign_id"],
                            "campaign_name": data['campaign_name'],
                            "organization_id": data["organization_id"],
                            "start_at": data["start_at"],
                            "end_at": data["end_at"],
                            "frequency": data["frequency"],
                            "transaction_limit": data["transaction_limit"],
                            "transaction_reamining": data["transaction_reamining"],
                            "last_crawed_at": last_craw_date,
                            "keyword": tempKeyword,
                            "keyword_exclude": tempKeywordExclude,
                        })
                    except Exception as e:
                        print(f"error in keyword data: {e}")

                if len(search_data) > 0:
                    try:
                        formatted_search_data = data_format.format_keyword_group_by_campaign(
                            raw_data=search_data
                        )

                        await scraping_data(search_data=formatted_search_data)

                        del formatted_search_data, raw_data, search_data

                    except Exception as e:
                        telegram_notify.send_to_x_private(
                            message=f"Twitter\n\n scraping not working \n\n {e}")
                else:
                    telegram_notify.send_to_x_work_process(
                        message="Twitter\n\n ไม่พบ Keywords ที่ต้องการกวาดข้อมูล.")

            except Exception as e:
                telegram_notify.send_to_x_private(
                    message=f"Twitter\n\n error in run\n\n {e}")

            time.sleep(60 * 30)

    except Exception as e:
        telegram_notify.send_to_x_private(
            message=f"Stop work: Error while loop\n\n{e}")
