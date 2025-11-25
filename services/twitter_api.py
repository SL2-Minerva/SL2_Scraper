from services import http_request as httpReq
from urllib.parse import quote

import json

x_ct_ids_search_timeline = [
    "P7MECY6kuDaLeH18qOKii0YhDAqOOfdo0BgX9E2kLUK+D1g/ULgUUmQEs9rXhUB76xlk7TweXgrjt5FecmQLujTGmVd8PA",
    "1lrt4GdNUd9ikZSVQQtLYq/I5eNn0B6BOfH+HaRNxKtX5rHWuVH9u43tWjM+bKmSAqCNBNWmtGiozglHRB4LUvHSl8BH1Q",
    "+nbBzEthffNOvbi5bSdnToPkyc9L/DKtFd3SMYhh6Id7yp36lX3Rl6HBdh8SQIW+LnehKPkeTqnaXRuMRIOsJW4YzZo8+Q",
    "+nbBzEthffNOvbi5bSdnToPkyc9L/DKtFd3SMYhh6Id7yp36lX3Rl6HBdh8SQIW+LjqmKPn3X5JBsJQxenQeGXf66/xW+Q",
    "pSmekxQ+IqwR4ufmMng4Edy7lpAUo23ySoKNbtc+t9gklcKlyiKOyP6eKUBNH9rhcRr+d6afhjVGyl0O3S20+OSWOFZvpg",
    "ePRDTsnj/3HMPzo776XlzAFmS03JfrAvl19QswrjagX5SB94F/9TFSND9J2Qwgc8rLcjqntrPshncnjjBzgMzgQX57mcew",
    "NLgPAoWvsz2Ac3Z3o+mpgE0qBwGFMvxj2xMc/0avJkm1BFM0W7MfWW8PuNHcjktw4Opv5jedvFmD+YNAQ2tA/kJo/WgTNw",
    "WtZhbOvB3VPuHRgZzYfH7iNEaW/rXJINtX1ykSjBSCfbaj1aNd1xNwFh1r+y4CUejoYGiFmCxLvQftC7cmlS5z2xw5UqWQ",
    "660RzUONSPM3Mje2yz3RoQLZzGkUK9SnD2gfxNxRt7UQ09yc0G53EnxDjGw6Tq9IZum2OeiFsAETYN32BvePj6nUGMGw6A",
    "7qgUyEaITfYyNzKzzjjUpAfcyWwRLtGiCm0awdlUsrAV1tmZ1WtyF3lGiWk/S6pNY/+zPO21gojmqMHwZWZNQhfIugD97Q",
    "zYs362WrbtURFBGQ7Rv3hyT/6k8yDfKBKU454vp3kZM29fq69khRNFplqkocaIluQO2QH84eBruYP4p3+p7zMQqKnh1tzg",
    "RAK+Yuwi51yYnZgZZJJ+Dq12Y8a7hHsIoMewa3P+GBq/fHMzf8HYvdPsI8OV4QDnyXMZlke9XQ2AF7/YfU+93/K+YOHjRw",
    "660RzUONSPM3Mje2yz3RoQLZzGkUK9SnD2gfxNxRt7UQ09yc0G53EnxDjGw6Tq9IZrq2OejVOAN8clJKXpdpto8j3Fc56A",
]

x_ct_ids_tweet_detail = [
    "/LoG2lSaX+QgJSCh3CrGthXO234DPMOwGH8I08tGoKIHxMuLx3lgBWtUm3stWbhfcSmhLv+ySNzB4fWGRkCqEDn4k46B/w",
    "ZZOSf+utOr1n65p+Sg2LccZfJ5/Vj68ph/xb7ya9FzI7hymTwQZ3ps8uBO8ydSrDfWg7t2bRzi+1IcEfrhkr7VHeTBS+Zg",
    "kovzsCG4k1iOqwWNDkMRhe6sPNpurD/GQb0KRYbHM03/jRtqwq86FkRuiidSrIMSp43MQJHVyVb4d9DXSK1Z05Ru8nOTkQ",
    "9MaAqggJNz2Rf3D1FVexWxSSQCBQAXBOJ8mEWgSw/WvUXGT69ZZ1OkmW7gOq1bFFosWqJvcDkyieoWUQ5FcqMDFktinF9w",
    "hkiaxN1DeK7jEa4dS72rZ8pT6vSdPa5oeJIfjphRdrCGOzp9u4yn6cPlcxAoDQwrNrrYVIWUy27ieMNxTyP7Pp4R9UkkhQ",
    "9l/Ltxn4iXh549AZ+VuVv5286Aev3I9ThiMTHY8jznam/EiLBfrPRaq+rkQYMYGTF72oJPWBvzPi7GxkNqitrK1UfvU49Q",
    "ev5PJB28BA5OUU50aS/s97oMi8oeE0ftyxu4MdErLAZFZP3JNGRl/NMPwS3+/79OVyEkqHn3bJN/yre6/46xN50QSPWweQ",
    "6ACyq4vUgI/xdrUn4mpU+8op+sQdvSqMrpB+4Hi0amK1xoNIYakhRODpH/u/Z6HQRYC2OuvQWwomEfwHHrKBBIBxNUpa6w",
    "yz3rhBM3nljtmseB7G8qywGKoZq9Cn+YobpmfUnmlaRcppu0oM+l4Ae67PuGKFfBc76VGchSksna6vJp++VCaw8n7hikyA",
    "PLCJLK/LC2a60kEBsdXiWYlNh8tmeo6ILrovhmdxcnpz46ycwkfzySoVAasC0I27dhlj7j+LgspUng45ZiAi1BFk9RJpPw",
    "i1Bh+Z1Wraphj6AbmK01sSdenA1AGI0J4t8luHS2flRghZTiVuVt+/jcVMXlenWMDsjUWYhSZZeSNKK//p2HiaCpIskRiA",
    "RtdtLk7UkmE59vri/ORqemD1cBV/faAc/UTCPLCAhdK+62gqhEwtJVpW7LN3UkAu8hYZlEUAq01cknAif13TyF6LmO3zRQ",
    "6XEj1VXFox5Yj03ffCMDaSGN1RfYzpcmou26Vq8SZQ26qBoTlBMgteKjU44aV9W0vrW2O+qUNHGBPEyH+geAQJeI879w6g",
    "dXCbpprcMJvXjAKAVXi0B8kOyCVTVXHAUZq4vZQLmwR26YVWwaVIqYxyK4nPtaWiwx4qp3bnfGlnSDEvxfJRrHyUQCXUdg",
    "mZx3SnYw3Hc7YO5suZRY6yXiJMm/uZ0svXZUUXjnd+iaBWm6LUmkRWCex2UjWUlOLxvGS5pfdEgGNJ3p+10M2qY0bITkmg",
    "QyqqsSfd7DhIoDJmn3uey+6BZlmAI6n/riBwpy/QzQolNC69YuTWRT0fG+Vkj35+d9MckUCDOomrVKWnSv2pGf493Tj3QA",
    "QlBivxgoLAqKR7i43Nu7cnO8fHoUu6blY/oJWDhLnyL4oDANCLGGoWTV+cFMyU3PT98dkEEl9SGeEea9ymUOJI4ShHE2QQ",
    "N+xeHUC6eYYR0pVuJElzDy23pCeS3he822HPuUnXwIcOX53WOlt9WWXKnE9tfBqbLplo5TRR0w/0F55E6JPk71iFHPNyNA",
    "+YzRG1VobMWZFhu2fat4AQjLKo1hdUwReQLBcUk6aHWosgifgYhRgbGBFeYzRyHVjEGmK/p62iId84GfnY7hwnFpsuTe+g"
]

# x_ct_ids_tweet_detail = [
#     "n6upTn07ffyCCYb/NR4ZC43xjb3cTXlnHmtUB1GsttGT5IUAlSa83BSLdjZAhJk0W4XP3ZsHdN9D6QrRVxiu/zDt090TnA",
#     "dRIjJNz0FwXgHBThdWOSJXMoo3zYbLmsFNL0/SRmjCpArox23JJtOf0lSslIMXOnNKw6N3EsacJM5ngth3MU/rfWbNXkdg",
#     "ZtkR15d19Qvr+aFtJnABkwms8F00AYH1Kps5ZVMdHB3HNEzZpzV5CFPzw4WDLB3bbS0pJGIEdWnmrNRIrx/vj1OVYCNuZQ",
#     "0tcwNcOJcslr7EEo2F7Tm5d7JOY+pvHVAt6MBUJl68FqPeiQXbZr1r9hSvZPS59wvSOckNY0UWVmmjmEv9clhnPKP1Sv0Q"
# ]

x_csrf_token = "1e679b01ed522b540926208c5c9e15cf5c10ed24f4513ea48f521f0ae22fe39765d9b73460beae3a2631a01174b08b03b3387d41ff9fada4845f81160f6ff8124345635a01c57f95428d816839d7f0bc"
bearer_token = "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
auth_token = "5a94b71103332a8dd64b0da86aa08f456039165f"

graphql_search_timeline_id = "yiE17ccAAu3qwM34bPYZkQ"
graphql_tweet_detail_id = "INsneb6y78uXRviWsuA-Rw"


def get_tweet_by_keyword(keyword="ลิซ่า", cursor=None, x_client_transaction_id=""):
    try:
        variables = {
            "rawQuery": keyword,
            "count": 40,
            "querySource": "typed_query",
            "product": "Latest"
        }

        if cursor:
            variables["cursor"] = cursor

        variables_encode = quote(json.dumps(variables))

        features = {
            "rweb_video_screen_enabled": False,
            "profile_label_improvements_pcf_label_in_post_enabled": True,
            "rweb_tipjar_consumption_enabled": True,
            "verified_phone_label_enabled": False,
            "creator_subscriptions_tweet_preview_api_enabled": True,
            "responsive_web_graphql_timeline_navigation_enabled": True,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "premium_content_api_read_enabled": False,
            "communities_web_enable_tweet_community_results_fetch": True,
            "c9s_tweet_anatomy_moderator_badge_enabled": True,
            "responsive_web_grok_analyze_button_fetch_trends_enabled": False,
            "responsive_web_grok_analyze_post_followups_enabled": True,
            "responsive_web_jetfuel_frame": False,
            "responsive_web_grok_share_attachment_enabled": True,
            "articles_preview_enabled": True,
            "responsive_web_edit_tweet_api_enabled": True,
            "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
            "view_counts_everywhere_api_enabled": True,
            "longform_notetweets_consumption_enabled": True,
            "responsive_web_twitter_article_tweet_consumption_enabled": True,
            "tweet_awards_web_tipping_enabled": False,
            "responsive_web_grok_show_grok_translated_post": False,
            "responsive_web_grok_analysis_button_from_backend": True,
            "creator_subscriptions_quote_tweet_preview_enabled": False,
            "freedom_of_speech_not_reach_fetch_enabled": True,
            "standardized_nudges_misinfo": True,
            "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
            "longform_notetweets_rich_text_read_enabled": True,
            "longform_notetweets_inline_media_enabled": True,
            "responsive_web_grok_image_annotation_enabled": True,
            "responsive_web_enhance_cards_enabled": False
        }
        features_url_encode = quote(json.dumps(features))

        url = f"https://x.com/i/api/graphql/{graphql_search_timeline_id}/SearchTimeline?variables={variables_encode}&features={features_url_encode}"

        response = httpReq.get(
            url=url,
            headers={
                "Authorization": f"Bearer {bearer_token}",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
                "sec-ch-ua-platform": "\"Windows\"",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua": "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Microsoft Edge\";v=\"134\"",
                "x-twitter-active-user": "yes",
                "x-twitter-client-language": "en",
                "x-client-transaction-id": x_client_transaction_id,
                "x-csrf-token": x_csrf_token,
            },
            cookies={
                "auth_token": auth_token,
                "ct0": x_csrf_token
            }
        )

        if response.status_code == 200:
            json_text = response.content.decode('utf-8-sig')
            json_data = json.loads(json_text)
            return json_data
        else:
            return {}
    except Exception as e:
        print(f"error in[service][twitter_api] fn get_tweet_by_keyword: {e}")
        return {}


def get_tweet_detail(tweet_id="1898643538822251004", cursor=None, x_client_transaction_id=""):
    variables = {
        "focalTweetId": f"{tweet_id}",
        "referrer": "search",
        "with_rux_injections": False,
        "rankingMode": "Relevance",
        "includePromotedContent": True,
        "withCommunity": True,
        "withQuickPromoteEligibilityTweetFields": True,
        "withBirdwatchNotes": True,
        "withVoice": True
    }

    if cursor:
        variables["cursor"] = cursor

    variables_encode = quote(json.dumps(variables))

    features = {
        "rweb_video_screen_enabled": False,
        "profile_label_improvements_pcf_label_in_post_enabled": True,
        "rweb_tipjar_consumption_enabled": True,
        "verified_phone_label_enabled": False,
        "creator_subscriptions_tweet_preview_api_enabled": True,
        "responsive_web_graphql_timeline_navigation_enabled": True,
        "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
        "premium_content_api_read_enabled": False,
        "communities_web_enable_tweet_community_results_fetch": True,
        "c9s_tweet_anatomy_moderator_badge_enabled": True,
        "responsive_web_grok_analyze_button_fetch_trends_enabled": False,
        "responsive_web_grok_analyze_post_followups_enabled": True,
        "responsive_web_jetfuel_frame": False,
        "responsive_web_grok_share_attachment_enabled": True,
        "articles_preview_enabled": True,
        "responsive_web_edit_tweet_api_enabled": True,
        "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
        "view_counts_everywhere_api_enabled": True,
        "longform_notetweets_consumption_enabled": True,
        "responsive_web_twitter_article_tweet_consumption_enabled": True,
        "tweet_awards_web_tipping_enabled": False,
        "responsive_web_grok_show_grok_translated_post": False,
        "responsive_web_grok_analysis_button_from_backend": True,
        "creator_subscriptions_quote_tweet_preview_enabled": False,
        "freedom_of_speech_not_reach_fetch_enabled": True,
        "standardized_nudges_misinfo": True,
        "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
        "longform_notetweets_rich_text_read_enabled": True,
        "longform_notetweets_inline_media_enabled": True,
        "responsive_web_grok_image_annotation_enabled": True,
        "responsive_web_enhance_cards_enabled": False
    }
    features_encode = quote(json.dumps(features))

    fieldToggles = {
        "withArticleRichContentState": True,
        "withArticlePlainText": False,
        "withGrokAnalyze": False,
        "withDisallowedReplyControls": False
    }
    fieldToggles_encode = quote(json.dumps(fieldToggles))

    url = f"https://x.com/i/api/graphql/{graphql_tweet_detail_id}/TweetDetail?variables={variables_encode}&features={features_encode}&fieldToggles={fieldToggles_encode}"
    response = httpReq.get(
        url=url,
        headers={
            "Authorization": f"Bearer {bearer_token}",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua": "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Microsoft Edge\";v=\"134\"",
            "x-twitter-client-language": "en",
            "x-twitter-active-user": "yes",
            "x-client-transaction-id": x_client_transaction_id,
            "x-csrf-token": x_csrf_token,
        },
        cookies={
            "auth_token": auth_token,
            "ct0": x_csrf_token
        }
    )

    if response.status_code == 200:
        json_text = response.content.decode('utf-8-sig')
        json_data = json.loads(json_text)

        return json_data
    else:
        print(response)
        return {}
