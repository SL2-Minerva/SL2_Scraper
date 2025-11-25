from datetime import datetime, date

import modules.line_notify as lineNotify


def is_in_range_date(start_at, end_at):
    try:
        today = date.today()

        if start_at != None and start_at != "" and end_at != None and end_at != "":
            # format start_at type
            if isinstance(start_at, str):
                start_at = datetime.strptime(start_at, "%Y-%m-%d")

            # format start_at type
            if isinstance(end_at, str):
                end_at = datetime.strptime(end_at, "%Y-%m-%d")

            if today >= start_at and today <= end_at:
                return True
            else:
                return False
        else:
            return False

    except Exception as e:
        lineNotify.send_to_scraper_problem(
            message=f"[Condition Error][is_in_range_date] {e}")

        return False


def is_in_transaction_limit(transaction_limit=0, transaction_remaining=0):
    try:
        infinite_limit = 99999999  # 8 digit

        if transaction_limit != None and transaction_remaining != None:
            if transaction_limit == infinite_limit:
                return True
            elif transaction_remaining > 0:
                return True
            else:
                return False
        else:
            return False

    except Exception as e:
        lineNotify.send_to_scraper_problem(
            message=f"[Condition Error][is_in_transaction_limit] {e}")

        return False


def is_out_of_frequency(frequency_minute=-1, last_craw_date=None):
    try:
        if last_craw_date != None and last_craw_date != "" and frequency_minute != -1 and frequency_minute != None and frequency_minute != "":
            # format data type
            if isinstance(last_craw_date, str):
                last_craw_date = datetime.strptime(
                    last_craw_date, "%Y-%m-%d %H:%M:%S").replace(minute=0, second=0)
            else:
                last_craw_date = last_craw_date.replace(minute=0, second=0)

            today = datetime.now()

            diff_minute = (today - last_craw_date).total_seconds() / 60

            if int(diff_minute) >= int(frequency_minute):
                return True
            else:
                return False
        else:
            return True
    except Exception as e:
        lineNotify.send_to_scraper_problem(
            message=f"[Condition Error][is_out_of_frequency] {e}")
        return False


def convert_to_number(s):
    suffixes = {'K': 1_000, 'k': 1_000, 'M': 1_000_000,
                'm': 1_000_000, 'B': 1_000_000_000, 'b': 1_000_000_000}

    if s[-1] in suffixes:
        numeric_part = float(s[:-1])
        multiplier = suffixes[s[-1]]

        return int(numeric_part * multiplier)
    else:
        return int(s)
