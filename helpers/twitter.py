import requests
import time
import re
from datetime import datetime


def get_tweet_data_api(url=""):
    def get_twimg_url(tweet_id=""):
        return f"https://cdn.syndication.twimg.com/tweet-result?id={tweet_id}&token=418g769m7fi&ukktdl=w08ypzw4loei"

    def get_fx_twitter_url(tweet_id=""):
        return f"https://api.fxtwitter.com/status/{tweet_id}"

    result = None

    try:
        tweet_id = url.split("/")[-1]
        url = get_fx_twitter_url(tweet_id=tweet_id)
        response = requests.get(url=url)

        if response.status_code == 200:
            result = response.json()

            # TODO: enable only fx twitter
            if result["code"] == 200:
                result = result["tweet"]

    except Exception as e:
        pass

    return result


def wait_for_next_minute():
    current_second = datetime.now().second

    waiting_seconds = 60 - current_second

    print(f"Waiting for {waiting_seconds} seconds to the next minute...")
    time.sleep(waiting_seconds)


def remove_tco_link_at_end(text):
    return re.sub(r'\s*https://t\.co/\S+\s*$', '', text).strip()
