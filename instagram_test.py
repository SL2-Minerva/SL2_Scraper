from datetime import datetime, timedelta

from urllib.parse import quote

import requests
import httpx
import random
import json
import asyncio
import os
import modules.file_handle as fileHandle
import formatters.data_format as dataFormat
import helpers.scraper as scraper
import modules.line_notify as lineNotify


async def run():
    # NEW:START
    # ds_user_id = "69017308251"
    # sessionid = "69017308251%3AEkb9AOIV8fZqPw%3A14%3AAYclZ8kSlO_eSex9V0N2tJU_FskS7-a7nAPYy7sI2A"
    # NEW:END

    current_time = datetime.now()
    if current_time.hour >= 12:
        ds_user_id = "69017308251"
        sessionid = "69017308251%3AEkb9AOIV8fZqPw%3A14%3AAYclZ8kSlO_eSex9V0N2tJU_FskS7-a7nAPYy7sI2A"
    else:
        ds_user_id = "67054051318"
        sessionid = "67054051318%3Accx7gOSfas1nuM%3A3%3AAYcEj_jR84u6pof8zXyK_RNXkJR5RunzdMxMj5bV_Q"

    user_agent_list = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36',    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_4_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1',    'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
                       'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edg/87.0.664.75',    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18363', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36']

    headers = {
        "User-Agent": user_agent_list[random.randint(0, len(user_agent_list)-1)],
        "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "*/*",
        "Cookie": f'ds_user_id={ds_user_id}; sessionid={sessionid}'
    }

    with httpx.Client(
        timeout=httpx.Timeout(20.0),
        headers=headers,
    ) as session:

        query_hash = "1780c1b186e2c37de9f7da95ce41bb67"
        variables = {
            "tag_name": "ก้าวไกล",
            "first": 1,
            "after": None,
        }
        variables_encoded = quote(json.dumps(variables))

        url = f"https://www.instagram.com/graphql/query/?query_hash={query_hash}&variables={variables_encoded}"

        print("1")

        result = session.get(url)
        data_content = json.loads(result.content)
        posts = data_content["data"]["hashtag"]["edge_hashtag_to_media"]
        for post in posts['edges']:
            # print json
            print(json.dumps(post["node"], indent=4, ensure_ascii=False))
        print(f"{(result)}")
        # * [NOTIFY]: Notify when have keyword to scraping
        lineNotify.send_to_scraper_daily_data(
            message=f"Instagram\n\n มีการสั่งให้ทำงาน จำนวน:{len(posts)} keyword."
        )
        # print(json.loads(result.content))

    # print("done")


asyncio.run(run())
