from facebook_scraper import *
import time
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#######################################################


def scraper_facebook(keyword):
    print("Start Facebook Crawl: ", keyword)
    # For MySQL connect

    os.chdir(os.path.dirname(__file__))
    path = os.getcwd() + '/'

    # cookie = "ps_l=1;usida=eyJ2ZXIiOjEsImlkIjoiQXNveHAwZmx3dDlidyIsInRpbWUiOjE3MzQ5MzU5OTN9;datr=38XcYgtH3hgZucYKovodPel9;fr=19TjM0gTiiFzlFfXh.AWWgwzs9_tRAz3MJ2jj_R6v6cD4.BnaUpt..AAA.0.0.BnaUpt.AWUk80u7Plw;xs=37%3A2eF8rhYx3YERDA%3A2%3A1726414199%3A-1%3A12003%3A%3AAcXtLsHB-1rwxOPsWhFK5pJk3iUtwRnbFW3D_89TgK_N;c_user=100004094239426;presence=C%7B%22t3%22%3A%5B%5D%2C%22utc3%22%3A1734953583412%2C%22v%22%3A1%7D;ar_debug=1;ps_n=1;sb=38XcYh8PZkZGi95Ndzvt5beI;wd=1920x919"
    # postFile = path + '/facebook.com_cookies.txt'
    # print(postFile)
    # with open(postFile, 'w') as file:
    #     file.writelines(cookie)

    # For get keyword
    os.chdir(os.path.dirname(__file__))
    path = os.getcwd() + '/'
    file = path+'/facebook.com_cookies.txt'
    set_cookies(file)

    try:
        for post in get_posts_by_search(
                keyword,
                # credentials=["tan2022@hotmail.com",
                #              "tHitipongpUrinsuwan6005a"],
                pages=3,
                options={
                    "comments": True,
                    "progress": True,
                    "reactors": True,
                    "comments_reactors": True,
                    "allow_extra_requests": True,
                    "reactions": True
                }):

            print(post)

    except Exception as e:
        print("Main Error: ", e)
