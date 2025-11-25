
from pymongo import UpdateOne
from datetime import datetime

import db.mongo as mongo
import modules.line_notify as lineNotify

import time


async def updatePostsAndCommentsData(data=[], campaign_id="", keyword_id=""):
    result = None

    try:
        collection_name = f"twitter_{campaign_id}_{keyword_id}"
        ___collection = mongo.get_db_driver()[collection_name]

        now_time_string = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # bulk_operations = [
        #     UpdateOne({'full_text': doc['full_text']}, {'$set': {**doc, "scraping_at": now_time_string}}, upsert=True) for doc in data
        # ]

        # result = ___collection.bulk_write(bulk_operations, ordered=False)

        # result = ___collection.insert_many(data)

        index = 0
        round = 10

        for doc in data:
            doc["scraping_at"] = now_time_string
            # ___collection.insert_one(doc)
            ___collection.update_one({'full_text': doc['full_text']}, {
                                     '$set': doc}, upsert=True)

            index += 1
            if (index % round) == 0:
                time.sleep(5)
            else:
                time.sleep(3)

    except Exception as e:
        if "Connection refused" in f"{e}":
            message = f"\nTwitter:\n\n รอการเชื่อมต่อ MongoDB"
            lineNotify.send_notify_scraping_result(message)
        else:
            message = f"\nTwitter:\n\nerror in connection mongodb {e}"
            lineNotify.send_to_scraper_problem(message)

        result = None

    return result
