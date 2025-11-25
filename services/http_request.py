from lxml import etree
from bs4 import BeautifulSoup

import requests
import json


def get(url, payload={}, headers=None, cookies=None):
    if cookies:
        cookie_str = "; ".join(
            [f"{key}={value}" for key, value in cookies.items()])
        headers["Cookie"] = cookie_str

    response = requests.request("GET", url, headers=headers, data=payload)

    return response


def get_dom_by_url(url):
    result = requests.get(url)
    html = result.content
    soup = BeautifulSoup(html, "html.parser")
    dom = etree.HTML(str(soup))

    return dom


def get_pantip_smart_search_dom(paging, keyword):
    important_key = "m7QpVS87V4hxuO3uXu7NuFagggrGGvCV8D%2Db8fLIlk79nWRszHeifuA41jRN3Lv6M%5Fv0tzOu8fN7CpmmG5wegHCQ%5FubOm5nLhyOFSqlc%5FuRZ0Ybpeg"
    paging_count = paging * 10

    url_search = f"https://search.pantip.com/ss?q={keyword}&s=&f={paging_count}&r=&y={important_key}"

    return get_dom_by_url(url_search)


def get_pantip_comments_by_topic_id(topic_id):
    # [example response]
    # {
    #     "count": 318,
    #     "check_pinit": "false",
    #     "paging": {
    #     },
    #     "comments": []
    # }

    comment_url_api = f"https://pantip.com/forum/topic/render_comments?tid={topic_id}"
    headers = {
        "x-requested-with": "XMLHttpRequest"
    }

    response = requests.post(comment_url_api, headers=headers)
    json_text = response.content.decode('utf-8-sig')
    json_data = json.loads(json_text)

    return json_data
