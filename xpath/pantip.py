__post_container = "//div[contains(@class,'main-post-inner')]"

# old version
# __comment_container = "//div[@id='comments-jsrender']//div[contains(@class,'display-post-wrapper')]"

__comment_container = "//div[@id='comments-jsrender']//div[@class='display-post-wrapper-inner']//div[@class='display-post-status-leftside']"
__comment_container_without_reply = "//div[@id='comments-jsrender']//div[contains(@class,'display-post-wrapper') and contains(@class,'section-comment') and not(contains(@class,'sub-comment'))]"
__comment_container_only_reply = "//div[@id='comments-jsrender']//div[contains(@class,'display-post-wrapper') and contains(@class,'sub-comment')]"


# ? [info] concat string with "https://search.pantip.com/"
def post_list_from_smart_search():
    return f"//table//table//p/a[not(contains(text(),'#'))]/@href"


def post_box_content(child=""):
    return f"{__post_container}{child}"


def post_topic_id():
    return "//input[@id='topicid_lead']/@value"


def post_url():
    return "//link[@rel='canonical']/@href"


def post_link():
    return "//ul[@id='list-change-view']//div[@class='pt-list-item__title']//h2//a[@href]"


def post_profile_image(only_xpath=False):
    xpath = f"//div[@class='display-post-avatar']/a/img/@src"

    if only_xpath:
        return xpath
    else:
        return post_box_content(xpath)


def post_title(only_xpath=False):
    xpath = f"//h2[@class='display-post-title']//text()"

    if only_xpath:
        return xpath
    else:
        return post_box_content(xpath)


def post_content(only_xpath=False):
    xpath = f"//div[@class='display-post-story']//text()"

    if only_xpath:
        return xpath
    else:
        return post_box_content(xpath)


def post_images(only_xpath=False):
    xpath = f"//img[@class='img-in-post']"

    if only_xpath:
        return xpath
    else:
        return post_box_content(xpath)


def post_youtube_videos(only_xpath=False):
    xpath = f"//a[@class='video_id']"

    if only_xpath:
        return xpath
    else:
        return post_box_content(xpath)


def post_datetime(only_xpath=False):
    xpath = f"//span[@class='display-post-timestamp']//abbr/@data-utime"

    if only_xpath:
        return xpath
    else:
        return post_box_content(xpath)


def post_account_name(only_xpath=False):
    xpath = f"//a[@class='display-post-name owner']/text()"

    if only_xpath:
        return xpath
    else:
        return post_box_content(xpath)


def post_like(only_xpath=False):
    xpath = f"//div[@class='display-post-emotion']//span[contains(@class,'emotion-score')]"

    if only_xpath:
        return xpath
    else:
        return post_box_content(xpath)


def post_engagements(only_xpath=False):
    # ? [INFO] [ถูกใจ(0), ขำกลิ้ง(1), หลงรัก(2), ซึ้ง(3), สยอง(4), ทึ่ง(5)]
    xpath = f"//div[@class='emotion-vote-list alt02']//span[@class='emotion-choice-score']"

    if only_xpath:
        return xpath
    else:
        return post_box_content(xpath)


def comment_box_content(child="", length=0):
    if length > 0:
        return f"({__comment_container})[{length}]{child}"
    else:
        return f"({__comment_container}){child}"


def comment_content(only_xpath=False, length=0):
    xpath = f"//div[@class='display-post-story']"

    if only_xpath:
        return xpath
    else:
        return comment_box_content(child=xpath, length=length)


def comment_images(only_xpath=False, length=0):
    xpath = f"//img[@class='img-in-post']"

    if only_xpath:
        return xpath
    else:
        return comment_box_content(child=xpath, length=length)


def comment_datetime(only_xpath=False, length=0):
    # return f"{__comment_container}//span[@class='display-post-timestamp']//abbr"
    xpath = f"//span[@class='display-post-timestamp']//abbr"

    if only_xpath:
        return xpath
    else:
        return comment_box_content(child=xpath, length=length)


def comment_account_name(only_xpath=False, length=0):
    # return f"{__comment_container}//div[@class='display-post-avatar-inner']//a[@class='display-post-name'][1]"
    xpath = f"//div[@class='display-post-avatar-inner']//a[@class='display-post-name'][1]"

    if only_xpath:
        return xpath
    else:
        return comment_box_content(child=xpath, length=length)


def comment_like(only_xpath=False, length=0):
    # return f"{__comment_container}//div[@class='display-post-emotion']//span[contains(@class,'emotion-score')]"
    xpath = f"//div[@class='display-post-emotion']//span[contains(@class,'emotion-score')]"

    if only_xpath:
        return xpath
    else:
        return comment_box_content(child=xpath, length=length)


def see_more_reply():
    return f"//a[@class='reply see-more']"
