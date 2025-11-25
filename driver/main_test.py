from selenium import webdriver
import sys
import signal
import os


def create_driver():
    # driver = webdriver.Chrome()
    chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument("--incognito")
    # chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument("--disable-application-cache")

    driver = webdriver.Chrome(options=chrome_options)
    return driver


def get_pid(driver):
    try:
        return int(driver.service.process.pid)
    except Exception as e:
        return 0


def kill_process(pid):
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"clear process id: {pid} [SUCCESS]")
    except:
        print(f"clear process id: {pid} [FAIL]")


def get_search_from_argv():
    q_search = [element for element in sys.argv if "-q=" in element]

    search = q_search[0].replace("-q=", "") if len(q_search) > 0 else "ก้าวไกล"
    return search


def get_paging_from_argv() -> int:
    try:
        q_page = [element for element in sys.argv if "-page=" in element]
        page = int(q_page[0].replace("-page=", "")) if len(q_page) > 0 else 10
    except Exception as e:
        page = 10
    return page


def get_platform_from_argv() -> str:
    try:
        q_platform = [
            element for element in sys.argv if "-platform=" in element]
        platform = q_platform[0].replace(
            "-platform=", "") if len(q_platform) > 0 else "all"
    except Exception as e:
        platform = "all"
    return platform


def get_video_count_from_argv() -> int:
    try:
        q_count = [element for element in sys.argv if "-vcount=" in element]
        vcount = int(q_count[0].replace("-vcount=", "")
                     ) if len(q_count) > 0 else 30
    except Exception as e:
        vcount = 30
    return vcount


def get_video_comment_count_from_argv() -> int:
    try:
        q_count = [element for element in sys.argv if "-ccount=" in element]
        vcount = int(q_count[0].replace("-ccount=", "")
                     ) if len(q_count) > 0 else 30
    except Exception as e:
        vcount = 30
    return vcount
