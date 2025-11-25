from datetime import datetime

import formatters.data_format as dataFormat
import psutil


def format_line_scraping_result(platform="", campaign_name="", keyword_name="", count_activity=""):
    date_time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    template = f"Data Scraper for {platform}"
    template += f"\nDate Crawler: {date_time_now}"
    template += f"\nCampaign: {campaign_name}"
    template += f"\nKeyword: {keyword_name} found {count_activity} result."

    return template


def format_campaign_result(platform="", campaign_name="", campaign_id=0, keyword="", datetime_start_campaign_scraping=datetime.now(), datetime_end_campaign_scraping=datetime.now(), total_result="", total_insert="", total_update=""):
    cpu_used = psutil.cpu_percent()
    datetime_diff = datetime_end_campaign_scraping - datetime_start_campaign_scraping
    diff_string = dataFormat.format_time_diff(
        diff_sec=datetime_diff.total_seconds())

    template = f"[FINISH]"
    template += f"\n\n{platform}"
    template += f"\n\nCampaign: {campaign_name}({campaign_id})"
    template += f"\nKeyword: {keyword}"
    template += f"\nResult:{total_result}"
    template += f"\nInsert:{total_insert}"
    template += f"\nUpdate:{total_update}"
    template += f"\n\nStart: {datetime_start_campaign_scraping.strftime('%Y-%m-%d %H:%M')}"
    template += f"\nEnd: {datetime_end_campaign_scraping.strftime('%Y-%m-%d %H:%M')}"
    template += f"\nTime used: {diff_string}"
    template += f"\nCPU used:{cpu_used}%"

    return template


def format_end_process(platform="", total_result="", datetime_start_campaign_scraping=datetime.now(), datetime_end_campaign_scraping=datetime.now()):
    try:
        datetime_diff = datetime_end_campaign_scraping - datetime_start_campaign_scraping
        diff_string = dataFormat.format_time_diff(
            diff_sec=datetime_diff.total_seconds())

        template = ""

        template += f"{platform}"
        template += f"\ncount:{total_result}"
        template += f"\nstart: {datetime_start_campaign_scraping.strftime('%Y-%m-%d %H:%M')}"
        template += f"\nend  : {datetime_end_campaign_scraping.strftime('%Y-%m-%d %H:%M')}"
        template += f"\ntime used: {diff_string}"

        return template
    except Exception as e:
        return f"Error format end process: {e}"
