from selenium import webdriver


def get_webdriver() -> webdriver.Chrome:
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--start-maximized')

    return webdriver.Chrome(options=chrome_options)


def set_window_size(driver: webdriver.Chrome):
    total_height = driver.execute_script("return document.body.scrollHeight")
    total_width = driver.execute_script("return document.body.scrollWidth")
    driver.set_window_size(total_width, total_height)
