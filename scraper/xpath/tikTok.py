def button_guest():
    return f'//*[@id="loginContainer"]/div/div/div[3]/div/div[2]'


def username_input():
    return f"//form//input[@name='username']"


def password_input():
    return f"//form//input[@type='password']"


def login_button():
    return f"//form//button[@data-e2e='login-button']"


def video_caption():
    return "//div[@data-e2e='search-card-video-caption']"


def video_link():
    return "//div[@id='tabs-0-panel-search_top']//div[@data-e2e='search_top-item']//a[@href]"


def replies_button():
    return "//div[contains(@class,'DivReplyActionContainer')]//p[@data-e2e='view-more-1']"


def replies_button_more():
    return "//div[contains(@class,'DivReplyActionContainer')]//p[@data-e2e='view-more-2']"


def verify_bar_close_button():
    return "//div[@id='tiktok-verify-ele']//a[@id='verify-bar-close']"


def modal_login_close_button():
    return "//div[@id='login-modal']//div[@data-e2e='modal-close-inner-button']"
