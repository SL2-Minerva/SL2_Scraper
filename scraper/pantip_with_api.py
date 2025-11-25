

from datetime import datetime
from modules import telegram_notify

import time
import services.pantip_api as pantipService
import services.keywords as keywordsService
import services.transaction as transactionService
import formatters.data_format as dataFormat
import formatters.line_format as lineFormat
import helpers.scraper as scraperHelper
import helpers.error_handle as errorHandle


async def scraping_data(search_data=[]):
    campaign_lists = search_data

    total_count_result = 0

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
        if not scraperHelper.is_in_range_date(start_at=start_at, end_at=end_at):
            continue

        # TODO: condition 2 check limit transaction remaining
        if not scraperHelper.is_in_transaction_limit(transaction_limit=transaction_limit, transaction_remaining=transaction_remaining):
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
            if not scraperHelper.is_out_of_frequency(frequency_minute=frequency, last_craw_date=last_craw_date):
                continue

            await transactionService.save_last_craw_at(
                keyword_id=keyword_id,
                source_id=transactionService.source_id_pantip
            )

            number_of_result = 0
            flag_error = []

            for keyword in keywords:
                temp_keywords.append(f"{keyword}({keyword_id})")

                data_result = []

                posts_and_comments_data = await pantipService.get_post_and_comment_data_api(
                    keyword=keyword,
                    keyword_id=keyword_id,
                    keyword_checks=keyword_checks,
                    keyword_excludes=keyword_excludes
                )

                data_result.extend(posts_and_comments_data)

                try:
                    number_of_result += len(data_result)

                    # todo: insert to database
                    if len(data_result) > 0:
                        insert_len, update_len = await transactionService.insert_post_and_comments_data_to_mysql(new_data=data_result)
                        total_insert += insert_len
                        total_update += update_len

                        # * insert to second database
                        await transactionService.insert_post_and_comments_data_to_mysql(new_data=data_result, isSecondDB=True)

                except Exception as e:
                    try:
                        result_message = errorHandle.handle(e)

                        if result_message["is_error"]:
                            if "ส่งถึง Developer" in result_message['message']:
                                flag_error.append(
                                    "ไม่สามารถเชื่อมต่อ mongodb ได้")
                            else:
                                flag_error.append(
                                    f"{result_message['message']}")

                    except Exception as ee:
                        pass

                time.sleep(1)

            flag_error_message = ""

            try:
                if number_of_result == 0:
                    flag_error = list(set(flag_error))
                    flag_error_message = ", ".join(flag_error)

            except Exception as e:
                pass

            await transactionService.pushTransactionScrapingResult(
                keyword_id=keyword_id,
                source_id=transactionService.source_id_pantip,
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
                line_message = lineFormat.format_campaign_result(
                    platform="Pantip",
                    campaign_name=campaign_name,
                    campaign_id=campaign_id,
                    keyword=keyword_str,
                    datetime_start_campaign_scraping=datetime_start_campaign_scraping,
                    datetime_end_campaign_scraping=datetime_end_campaign_scraping,
                    total_result=total_result,
                    total_insert=total_insert,
                    total_update=total_update,
                )
                telegram_notify.send_to_pantip_work_process(
                    message=line_message)

            except Exception as e:
                telegram_notify.send_to_pantip_private(
                    message=f"error format_campaign_result:\n\nPantip\n\nerror:\n{e}")

        total_count_result += total_result

        time.sleep(2)

    return total_count_result


async def run():
    try:
        print("Pantip scraping call to start.")
        telegram_notify.send_to_pantip_work_process(
            message="Pantip scraping call to start.")

        while True:
            try:
                raw_data = await keywordsService.getActiveKeyword(platform=keywordsService.platform_pantip)
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
                            last_craw_date = await keywordsService.get_last_craw_date(keyword_id=data["id"], source_id=transactionService.source_id_pantip)

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
                        telegram_notify.send_to_pantip_private(
                            message=f"WARNING PANTIP:\n\n in loop format raw data \n\n {e}")

                if len(search_data) > 0:
                    try:
                        formatted_search_data = dataFormat.format_keyword_group_by_campaign(
                            raw_data=search_data
                        )

                        await scraping_data(search_data=formatted_search_data)

                        del formatted_search_data, raw_data, search_data

                    except Exception as e:
                        telegram_notify.send_to_pantip_private(
                            message=f"Pantip\n\n scraping not working \n\n {e}")

                else:
                    telegram_notify.send_to_pantip_work_process(
                        message=f"Pantip\n\n ไม่พบ Keywords ที่ต้องการกวาดข้อมูล.")

            except Exception as e:
                telegram_notify.send_to_pantip_private(
                    message=f"Pantip error: out\n\n {e}")

            time.sleep(60 * 30)

    except Exception as e:
        telegram_notify.send_to_pantip_private(
            message=f"Error while loop\n\n{e}")
