
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from datetime import datetime, timedelta

# import random
import json
import requests
import time
import driver.main as driverInstant
import xpath.pantip as xpathPantip
import services.pantip_api as pantipService
import services.keywords as keywordsService
import services.transaction as transactionService
import modules.file_handle as fileHandle
import modules.segmentation as segmentation
import modules.line_notify as lineNotify
import formatters.data_format as dataFormat
import formatters.line_format as lineFormat
import formatters.pantip_format as pantipFormat
import helpers.scraper as scraperHelper
import helpers.error_handle as errorHandle


async def run():
    try:
        print("Pantip Api is started.")

        if await check_process_running():
            print("Pantip have process running already. Exit.")

            lineNotify.send_to_scraper_daily_data(
                message=f"Pantip\n\n มีกระบวนการกวาดข้อมูลทำงานอยู่แล้ว."
            )
            exit()
        else:
            print("Pantip Api is continue running.")
            await set_process_status(
                status="1"
            )

        paging = driverInstant.get_paging_from_argv()

        raw_data = await keywordsService.getActiveKeyword()
        search_data = []

        for data in raw_data:
            try:
                tempKeyword = []
                tempKeywordExclude = []

                if isinstance(data["name"], str) and data["name"] != "":
                    tempKeyword = data["name"].split(",")

                if isinstance(data["keyword_exclude"], str) and data["keyword_exclude"] != "":
                    tempKeywordExclude = data["keyword_exclude"].split(",")

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
                lineNotify.send_notify_to_dev(
                    message=f"WARNING PANTIP:\n\n in loop format raw data \n\n {e}")

        if len(search_data) > 0:
            try:
                formatted_search_data = dataFormat.format_keyword_group_by_campaign(
                    raw_data=search_data
                )

                await scraping_data(search_data=formatted_search_data, paging=paging)
            except Exception as e:
                lineNotify.send_notify_to_dev(
                    message=f"Pantip\n\n scraping not working \n\n {e}")
        else:
            lineNotify.send_to_scraper_process(
                message=f"Pantip\n\n ไม่พบ Keywords ที่ต้องการกวาดข้อมูล.")

        await set_process_status(
            status="0"
        )
    except Exception as e:
        lineNotify.send_to_scraper_problem(
            message=f"Pantip\n\n Error\n{e}.")
        await set_process_status(
            status="0"
        )


async def check_process_running():
    try:
        status = await fileHandle.read_process_status(
            platform=fileHandle.process_pantip)

        if status == "1":
            return True
        else:
            return False
    except Exception as e:
        message_err = f"Pantip\n\n error on check_process_status\n\n {e}"
        lineNotify.send_to_scraper_problem(message=message_err)

        return False


async def set_process_status(status="0"):
    try:
        await fileHandle.write_process_status(
            status=status, platform=fileHandle.process_pantip)
    except Exception as e:
        message_err = f"Pantip\n\n error on set_process_status\n\n {e}"
        lineNotify.send_to_scraper_problem(message=message_err)


async def scraping_data(search_data=[], paging=1):
    campaign_lists = search_data

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
            # lineNotify.send_to_scraper_process(
            #     message=f"Pantip\n\n Campaign: {campaign_name} ไม่เข้าเงือนไขช่วงเวลา.\n\n{start_at} - {end_at}")
            continue

        # TODO: condition 2 check limit transaction remaining
        if not scraperHelper.is_in_transaction_limit(transaction_limit=transaction_limit, transaction_remaining=transaction_remaining):
            # lineNotify.send_to_scraper_process(
            #     message=f"Pantip\n\n Campaign: {campaign_name} ไม่เข้าเงือนไข limit\n\n transaction_limit:{transaction_limit}\n transaction_remaining:{transaction_remaining}")
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
                # lineNotify.send_to_scraper_process(
                #     message=f"Pantip\n\n Campaign: {campaign_name} Keyword:{keywords}\nไม่เข้าเงือนไข frequency\n\n frequency:{frequency}\n last_craw_date:{last_craw_date}")
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

                posts_data = await pantipService.get_posts_data(
                    keyword=keyword,
                    paging=paging,
                    keyword_checks=keyword_checks,
                    keyword_excludes=keyword_excludes
                )
                data_result.extend(posts_data)

                for post in posts_data:
                    comments = await pantipService.get_comment_data_api(
                        url=post["url"],
                        keyword_checks=keyword_checks,
                        keyword_excludes=keyword_excludes
                    )
                    data_result.extend(comments)

                try:
                    number_of_result += len(data_result)

                    # todo: insert to database
                    if len(data_result) > 0:
                        await transactionService.updatePostsAndCommentsData(
                            data=data_result,
                            collection_name=transactionService.collection_name_pantip,
                            campaign_id=campaign_id,
                            keyword_id=keyword_id
                        )

                except Exception as e:
                    # todo: =============> START: handle error <============
                    try:
                        result_message = errorHandle.handle(e)

                        if result_message["is_error"]:
                            if "ส่งถึง Developer" in result_message['message']:
                                msg = f"Pantip\n\nupdatePostsAndCommentsData:\n{keyword}\n\n{result_message['message']}"
                                lineNotify.send_to_scraper_problem(message=msg)

                                flag_error.append(
                                    "ไม่สามารถเชื่อมต่อ mongodb ได้")
                            else:
                                flag_error.append(
                                    f"{result_message['message']}")

                    except Exception as ee:
                        message_err = f"Pantip\n\n error on errorHandle\n\n {ee}"
                        lineNotify.send_to_scraper_problem(message=message_err)
                    # todo: =============> END: handle error <============

                time.sleep(1)

            flag_error_message = ""

            try:
                if number_of_result == 0:
                    flag_error = list(set(flag_error))
                    flag_error_message = ", ".join(flag_error)

            except Exception as e:
                lineNotify.send_to_scraper_problem(
                    message=f"Pantip\n\n error on set flag_error_message\n\n {e}")

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
                    total_result=total_result
                )
                lineNotify.send_to_scraper_process(message=line_message)
            except Exception as e:
                lineNotify.send_to_scraper_daily_data(
                    message=f"[FINISH][ERROR]\n\nPantip\n\nerror:\n{e}")
        time.sleep(2)
