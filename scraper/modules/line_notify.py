
import requests

url = 'https://notify-api.line.me/api/notify'

line_token_scraper_process = "BzL3dYqguB8Sj6LyHd4U8KstKCcg3tWaRTjSlsqMl4E"
line_token_scraper_problem = "9I27RJyAoStVOZvnkC3P94mXprouijep9Kb95mk8Doi"
line_token_dev = "klDxwYEdspQZ5dIQ51fH0PyK12U0syRvkbrSFivjb3T"
line_token_cornea = "tkQKld9mOkvi7orhYFDSm9IIQEnH03GGX5dSM4rlSL4"
line_token_scraper_daily_data = "yjvFp5PqD3V36gix4UNyPTS9rbt5rWiwt5l66xXDRgM"

version = "v. 2.9"


def get_headers(token=""):
    headers = {
        'content-type':
            'application/x-www-form-urlencoded',
            'Authorization': 'Bearer '+token
    }

    return headers


def send_message(message="", token=""):
    try:
        headers = get_headers(token)
        data = {
            'message': message
        }

        r = requests.post(url, headers=headers, data=data)

        return r.text
    except Exception as e:
        return None


def send_notify_scraping_result(message=""):
    token_list = [line_token_cornea]

    for token in token_list:
        send_message(message=message, token=token)


def send_notify_to_dev(message=""):
    send_message(
        message=f"\n\n{message}\n\n{version}", token=line_token_dev)


def send_to_scraper_process(message=""):
    send_message(
        message=f"\n\n{message}\n\n{version}", token=line_token_scraper_process)


def send_to_scraper_problem(message=""):
    send_message(
        message=f"\n\n{message}\n\n{version}", token=line_token_scraper_problem)


def send_to_scraper_daily_data(message=""):
    send_message(
        message=f"\n\n{message}\n\n{version}", token=line_token_scraper_daily_data)
