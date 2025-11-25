def username_input():
    return "//input[@class='r-30o5oe r-1dz5y72 r-13qz1uu r-1niwhzg r-17gur6a r-1yadl64 r-deolkf r-homxoj r-poiln3 r-7cikom r-1ny4l3l r-t60dpp r-fdjqy7']"


def password_input():
    return "//input[@class='r-30o5oe r-1dz5y72 r-13qz1uu r-1niwhzg r-17gur6a r-1yadl64 r-deolkf r-homxoj r-poiln3 r-7cikom r-1ny4l3l r-t60dpp r-fdjqy7']"


def next_button():
    # return "//button[@role='button'][@style='background-color: rgb(15, 20, 25); border-color: rgba(0, 0, 0, 0);']"
    return '//*[@id="layers"]/div/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div/div/div/button[2]'


def login_button():
    return "//button[@data-testid='LoginForm_Login_Button']"


def post_link():
    return "//article[@data-testid='tweet' and @tabindex='0']//div[@class='css-175oi2r r-18u37iz r-1q142lx']//a[@role='link']"


def post_box_content(child=""):
    return f"//article[@tabindex='-1' and @data-testid='tweet']{child}"


def post_account_name(only_xpath=False):
    xpath = f"//a[@role='link' and @class='css-175oi2r r-1wbh5a2 r-dnmrzs r-1ny4l3l r-1loqt21']//span[@class='css-1jxf684 r-dnmrzs r-1udh08x r-3s2u2q r-bcqeeo r-1ttztb7 r-qvutc0 r-poiln3']"

    if only_xpath:
        return xpath
    else:
        return post_box_content(xpath)


def post_account_profile_img(only_xpath=False):
    xpath = "//a[@tabindex='-1']//img[@draggable]"

    if only_xpath:
        return xpath
    else:
        return post_box_content(xpath)


def post_screen_name(only_xpath=False):
    xpath = "//div[@data-testid='User-Name']//a[@role='link' and @tabindex='-1']//span"

    if only_xpath:
        return xpath
    else:
        return post_box_content(xpath)


def post_detail(only_xpath=False):
    xpath = "//div[@data-testid='tweetText']"

    if only_xpath:
        return xpath
    else:
        return post_box_content(xpath)


def post_detail_image(only_xpath=False):
    xpath = "//div[@data-testid='tweetPhoto']//img[@class='css-9pa8cd']"

    if only_xpath:
        return xpath
    else:
        return post_box_content(xpath)


def post_photo(only_xpath=False):
    xpath = "//div[@data-testid='tweetPhoto']//img"

    if only_xpath:
        return xpath
    else:
        return post_box_content(xpath)


def post_datetime(only_xpath=False):
    xpath = "//div[@class='css-146c3p1 r-bcqeeo r-1ttztb7 r-qvutc0 r-37j5jr r-a023e6 r-rjixqe r-16dba41']//time"

    if only_xpath:
        return xpath
    else:
        return post_box_content(xpath)


# index 0 for  views count.
def post_view(only_xpath=False):
    xpath = f"//span[@data-testid='app-text-transition-container']/span/span"

    if only_xpath:
        return xpath
    else:
        return post_box_content(xpath)


def post_like(only_xpath=False):
    xpath = "//button[@data-testid='like']"

    if only_xpath:
        return xpath
    else:
        return post_box_content(xpath)


def post_retweet(only_xpath=False):
    xpath = "//button[@data-testid='retweet']"

    if only_xpath:
        return xpath
    else:
        return post_box_content(xpath)


def post_reply_count(only_xpath=False):
    xpath = "//button[@data-testid='reply']"

    if only_xpath:
        return xpath
    else:
        return post_box_content(xpath)


def post_bookmark_count(only_xpath=False):
    xpath = "//button[@data-testid='bookmark']"

    if only_xpath:
        return xpath
    else:
        return post_box_content(xpath)


def comment_box_content(child="", length=0):
    if length > 0:
        return f"(//article[@tabindex='0' and @data-testid='tweet'])[{length}]{child}"
    else:
        return f"//article[@tabindex='0' and @data-testid='tweet']{child}"


def comment_account_name(only_xpath=False, length=0):
    xpath = "//div[@class='css-175oi2r r-1awozwy r-18u37iz r-1wbh5a2 r-dnmrzs']//a[@role='link']//div[@dir='ltr' and contains(@class,'r-1udh08x')]/span"

    if only_xpath:
        return xpath
    else:
        return comment_box_content(child=xpath, length=length)


def comment_account_profile_img(only_xpath=False, length=0):
    xpath = "//img[@draggable]"

    if only_xpath:
        return xpath
    else:
        return comment_box_content(child=xpath, length=length)


def comment_screen_name(only_xpath=False, length=0):
    xpath = "//div[@data-testid='User-Name']//a[@role='link' and @tabindex='-1']//span"

    if only_xpath:
        return xpath
    else:
        return comment_box_content(child=xpath, length=length)


def comment_content(only_xpath=False, length=0):
    xpath = "//div[@data-testid='tweetText']"

    if only_xpath:
        return xpath
    else:
        return comment_box_content(child=xpath, length=length)


def comment_content_photo(only_xpath=False, length=0):
    xpath = "//div[@data-testid='tweetPhoto' or @data-testid='card.layoutLarge.media']//img"

    if only_xpath:
        return xpath
    else:
        return comment_box_content(child=xpath, length=length)


def comment_view():
    return f"//article[contains(@class,'css-1dbjc4n') and contains(@class,'r-6416eg') and contains(@class,'r-o7ynqc')]//div[@role='group']//div[@class='css-1dbjc4n r-18u37iz r-1h0z5md'][4]"


def comment_like(only_xpath=False, length=0):
    xpath = "//div[@role='group']//button[@data-testid='like']"

    if only_xpath:
        return xpath
    else:
        return comment_box_content(child=xpath, length=length)


def comment_reply(only_xpath=False, length=0):
    xpath = "//div[@role='group']//button[@data-testid='reply']"

    if only_xpath:
        return xpath
    else:
        return comment_box_content(child=xpath, length=length)


def comment_view(only_xpath=False, length=0):
    xpath = "//div[@role='group']//a[@role='link']"

    if only_xpath:
        return xpath
    else:
        return comment_box_content(child=xpath, length=length)


def comment_retweet(only_xpath=False, length=0):
    xpath = "//div[@role='group']//button[@data-testid='retweet']"

    if only_xpath:
        return xpath
    else:
        return comment_box_content(child=xpath, length=length)


def comment_datetime(only_xpath=False, length=0):
    xpath = "//a[@role='link'][@dir='ltr']/time"

    if only_xpath:
        return xpath
    else:
        return comment_box_content(child=xpath, length=length)


def comment_link(only_xpath=False, length=0):
    xpath = "//div[@data-testid='User-Name']//a[@role='link'][@dir='ltr']"

    if only_xpath:
        return xpath
    else:
        return comment_box_content(child=xpath, length=length)


def show_more_comment():
    return f"//div[@role='button' and @class='css-18t94o4 css-1dbjc4n r-1777fci r-1pl7oy7 r-1ny4l3l r-o7ynqc r-6416eg r-13qz1uu']"


def show_reply_comment():
    return f"//div[@class='css-901oao r-1cvl2hr r-37j5jr r-a023e6 r-16dba41 r-rjixqe r-bcqeeo r-5njf8e r-qvutc0']"
    # return f"//div[@class='css-901oao']"
