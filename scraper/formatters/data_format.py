import scraper.modules.line_notify as lineNotify


def format_notify_keyword_campaign(data=[]):
    temp_result = []

    for item in data:
        temp_data = {
            "campaign_name": item["campaign_name"],
            "start_at": f'{item["start_at"]}',
            "end_at": f'{item["end_at"]}',
            "frequency": item["frequency"],
            "transaction_limit": item["transaction_limit"],
            "transaction_reamining": item["transaction_reamining"],
            "last_crawed_at": f'{item["last_crawed_at"]}',
            "condition_1": "na",
            "condition_2": "na",
            "condition_3": "na",
            "keywords": list(map(lambda x: {"keyword": x, "result": "na"}, item["keyword"])),
        }

        temp_result.append(temp_data)

    return temp_result


def format_keyword_group_by_campaign(raw_data=[]):
    formatted_data = []

    try:
        for data in raw_data:
            index = None

            for item in formatted_data:
                if item["campaign_id"] == data["campaign_id"]:
                    index = formatted_data.index(item)
                    break

            if index is not None:
                formatted_data[index]["keywords"].append({
                    "keyword_id": data["keyword_id"],
                    "keywords": data["keyword"],
                    "keyword_excludes": data["keyword_exclude"],
                    "last_crawed_at": data["last_crawed_at"],
                })
            else:
                formatted_data.append({
                    "campaign_id": data["campaign_id"],
                    "campaign_name": data['campaign_name'],
                    "organization_id": data["organization_id"],
                    "start_at": data["start_at"],
                    "end_at": data["end_at"],
                    "frequency": data["frequency"],
                    "transaction_limit": data["transaction_limit"],
                    "transaction_reamining": data["transaction_reamining"],
                    "keywords": [{
                        "keyword_id": data["keyword_id"],
                        "keywords": data["keyword"],
                        "keyword_excludes": data["keyword_exclude"],
                        "last_crawed_at": data["last_crawed_at"],
                    }],
                })
    except Exception as e:
        message_err = f"Scraping not working \n\n {e}"
        lineNotify.send_notify_to_dev(message=message_err)

    return formatted_data


def format_line_notify_result(data=[]):
    template = ""
    index = 0
    for item in data:
        index = index + 1
        template += f"\n\n\n{index}.Campaign: {item['campaign_name']}"
        template += f"\nStart At: {item['start_at']}"
        template += f"\nEnd At: {item['end_at']}"
        template += f"\nFrequency: {item['frequency']}"
        template += f"\nTransaction Limit: {item['transaction_limit']}"
        template += f"\nTransaction Remaining: {item['transaction_reamining']}"
        template += f"\nLast Crawed At: {item['last_crawed_at']}"
        template += f"\nCondition 1: {item['condition_1']}"
        template += f"\nCondition 2: {item['condition_2']}"
        template += f"\nCondition 3: {item['condition_3']}"
        template += f"\nKeywords: "
        for keyword in item["keywords"]:
            template += f"\n- {keyword['keyword']} found {keyword['result']} result."

    return template


def format_time_diff(diff_sec):
    days, hours, minutes, seconds = 0, 0, 0, 0
    days, remainder = divmod(diff_sec, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours)}:{int(minutes)}:{int(seconds)}"


def set_keyword_result(data=[], campaign_name_to_find="", keyword_to_find="", number_of_result=0):
    for item in data:
        if item["campaign_name"] == campaign_name_to_find:
            for keyword in item["keywords"]:
                if keyword["keyword"] == keyword_to_find:
                    keyword["result"] = number_of_result
                    break

    return data


def set_campaign_condition_result(data=[], campaign_name_to_find="", condition_to_find="", condition_result=""):
    for item in data:
        if item["campaign_name"] == campaign_name_to_find:
            item[condition_to_find] = condition_result
            break

    return data


def set_keyword_error(data=[], type_error="", keyword=""):
    selected_index = -1
    i = 0

    # todo: find index of type error in data
    for item in data:
        try:
            if item["type_error"] == type_error:
                selected_index = i
                break
        except:
            pass

        i += 1

    # todo: if found, append keyword to the list / if not, create new one
    if selected_index != -1:
        data[selected_index]["keywords"].append(keyword)
        data[selected_index]["keywords"] = list(
            set(data[selected_index]["keywords"]))
    else:
        data.append({
            "type_error": type_error,
            "keywords": [keyword]
        })

    return data
