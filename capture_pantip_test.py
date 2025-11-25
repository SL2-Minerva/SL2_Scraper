from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
from io import BytesIO

import time
import asyncio

import helpers.webdriver_helper as webdriver_helper


def capture(url: str, message_id: str, ref_id: str, is_comment: bool):
    driver = webdriver_helper.get_webdriver()
    driver.get(url)
    webdriver_helper.set_window_size(driver)

    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='display-post-wrapper main-post type']")))

        full_image_height = 0

        post_element = driver.find_element(
            By.XPATH, '//div[@class="display-post-wrapper main-post type"]')

        print(f"post capturing...")
        post_data_image = Image.open(BytesIO(post_element.screenshot_as_png))
        full_image_height += post_data_image.size[1]

        if is_comment:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='comments-jsrender']//div[@class='display-post-wrapper-inner']")))

            comment_xpath = f"(//div[@id='comments-jsrender']//div[@class='display-post-wrapper-inner'])[{message_id}]"
            comment_element = driver.find_element(By.XPATH, comment_xpath)

            print(f"comment capturing...")
            comment_data_image = Image.open(
                BytesIO(comment_element.screenshot_as_png))
            full_image_height += comment_data_image.size[1]

        full_image = Image.new(
            "RGB", (post_data_image.size[0], full_image_height))

        y_offset = 0
        full_image.paste(post_data_image, (0, y_offset))

        if is_comment:
            y_offset += post_data_image.size[1]
            full_image.paste(comment_data_image, (0, y_offset))

        now_date_time = time.strftime("%Y%m%d_%H%M")

        if is_comment:
            file_name = f"{message_id}_{ref_id}_{now_date_time}.jpeg"
        else:
            file_name = f"{message_id}_{now_date_time}.jpeg"

        full_image.save(f"{file_name}")

        del post_data_image
        del full_image

        if is_comment:
            del comment_data_image
    except Exception as e:
        print(e)

    driver.quit()


async def run():
    data = [
        {
            "id": 1,
            "message_url": "https://pantip.com/topic/43334566",
            "message_id": "43334566",
            "ref_id": None,
            "message_type": "post"
        },
        {
            "id": 2,
            "message_url": "https://pantip.com/topic/43334566/comment1",
            "message_id": "1",
            "ref_id": "43334566",
            "message_type": "comment"
        }
    ]

    for d in data:
        capture(
            url=d["message_url"],
            message_id=d["message_id"],
            ref_id=d["ref_id"],
            is_comment=d["message_type"].lower() == "comment"
        )

    print("Done")


asyncio.run(run())
