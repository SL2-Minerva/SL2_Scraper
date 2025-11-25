import helpers.twitter as twitterHelper
import formatters.twitter_format as twitterFormat


async def get_post_detail_from_api(topic_url=""):
    data_return = None

    try:
        data_result = twitterHelper.get_tweet_data_api(url=topic_url)

        if data_result is not None:
            twitter_data = twitterFormat.format_data_fx_tweet(
                data=data_result
            )

            is_pass_2 = False
            is_excluded_2 = False

            content = twitter_data["full_text"]

            if content == "" or content == " " or content == None:
                is_pass_2 = False

            if (not is_excluded_2) and is_pass_2:
                data_return = twitter_data

    except Exception as e:
        pass

    return data_return
