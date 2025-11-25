
import asyncio
import services.keywords as keywordsService
import modules.line_notify as lineNotify


async def run():
    print("run...")

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
                last_craw_date = await keywordsService.getLastCrawDate(keyword_id=data["id"], source_id=6)

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
            message_err = f"WARNING:\n\n in loop format raw data \n\n {e}"
            lineNotify.send_notify_to_dev(message=message_err)

    lineNotify.send_to_scraper_problem(f"{raw_data}")
    lineNotify.send_to_scraper_problem(f"{search_data}")


asyncio.run(run())
