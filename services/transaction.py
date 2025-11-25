from datetime import datetime
from modules import telegram_notify

import db.mysql as mysql
import modules.line_notify as lineNotify
import formatters.mysql_format as mysql_format


source_id_facebook = 1
source_id_twitter = 2
source_id_youtube = 3
source_id_instagram = 4
source_id_pantip = 6
source_id_tiktok = 7

media_type_text = 1
media_type_picture = 2
media_type_voice = 3
media_type_video = 4

collection_name_facebook = "facebook"
collection_name_twitter = "twitter"
collection_name_youtube = "youtube"
collection_name_instagram = "instagram"
collection_name_pantip = "pantip"
collection_name_tiktok = "tiktok"


async def select_data_exits_in_mysql(new_data=[], isSecondDB=False):
    data_exits = []

    try:
        field = "message_id, reference_message_id, source_id"
        data_select = ",".join(["(%s,%s,%s)" for d in new_data])

        flat_data = []
        for d in new_data:
            flat_data.extend([str(d[0]), str(d[1]), d[5]])

        sql = f"SELECT {field} FROM tbl_messages " \
            f"WHERE ({field}) IN " \
            f"({data_select});"

        if isSecondDB:
            connection = mysql.new_connection_second_db()
        else:
            connection = mysql.new_connection()

        cursor = connection.cursor()

        cursor.execute(sql, flat_data)

        data_exits = cursor.fetchall()  # [(1, 2, 1), (3, 4, 2), ...]

        connection.commit()
        cursor.close()
        connection.close()

    except Exception as e:
        err_message = f"error transaction.select_data_exits_in_mysql()\n\n {e}"

        print(err_message)
        telegram_notify.send_to_private(message=err_message)

    return data_exits


async def classify_insert_or_update_data(new_data=[], isSecondDB=False):
    data_insert = []
    data_update = []

    data_insert_check = []

    try:
        data_exits_in_mysql = await select_data_exits_in_mysql(new_data, isSecondDB=isSecondDB)

        for d in new_data:
            data_check = (str(d[0]), str(d[1]), d[5])

            if data_check in data_exits_in_mysql or data_check in data_insert_check:
                data_update.append(d)
            else:
                data_insert.append(d)
                data_insert_check.append(data_check)

    except Exception as e:
        err_message = f"error transaction.classify_insert_or_update_data()\n\n {e}"
        telegram_notify.send_to_private(message=err_message)

    del data_insert_check

    return data_insert, data_update


async def insert_data_to_mysql(new_data=[], isSecondDB=False):
    try:
        if len(new_data) == 0:
            return

        if isSecondDB:
            connection = mysql.new_connection_second_db()
        else:
            connection = mysql.new_connection()

        cursor = connection.cursor()

        data_value = ",".join(
            ["(" + ",".join(["%s"] * 19) + ")"] * len(new_data))

        sql = mysql_format.get_insert_sql_message(data_value)

        flat_data = [item for sublist in new_data for item in sublist]

        cursor.execute(sql, flat_data)

        connection.commit()
        cursor.close()
        connection.close()

    except Exception as e:
        err_message = f"error transaction.insert_data_to_mysql()\n\n {e}"

        print(err_message)
        telegram_notify.send_to_private(message=err_message)


async def update_data_to_mysql(new_data=[], isSecondDB=False):
    try:
        if len(new_data) == 0:
            return

        flat_data = []

        sql_select_first_row = f"SELECT "\
            "%s AS message_id, "\
            "%s AS reference_message_id, "\
            "%s AS source_id, "\
            ""\
            "%s AS full_message, "\
            "%s AS number_of_shares, "\
            "%s AS number_of_comments, "\
            "%s AS number_of_reactions, "\
            "%s AS number_of_views, "\
            "%s AS updated_at "

        flat_data.extend([
            new_data[0][0], new_data[0][1], new_data[0][5],
            new_data[0][6], new_data[0][12], new_data[0][13],
            new_data[0][14], new_data[0][15], datetime.now()
        ])

        sql_select_other_row = ""

        if len(new_data) > 1:
            sql_select_other_row = "UNION ALL " + "UNION ALL ".join(
                ["SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s " for d in new_data[1:]])

            for d in new_data[1:]:
                flat_data.extend([
                    d[0], d[1], d[5],
                    d[6], d[12], d[13],
                    d[14], d[15], datetime.now()
                ])

        sql_join_select = "SELECT * FROM ( " \
            f"{sql_select_first_row} " \
            f"{sql_select_other_row} "\
            ") AS temp "

        sql_on = ""\
            "t.message_id = v.message_id " \
            "AND t.reference_message_id = v.reference_message_id " \
            "AND t.source_id = v.source_id "

        sql_set = ""\
            "t.full_message = v.full_message, "\
            "t.number_of_shares = v.number_of_shares, "\
            "t.number_of_comments = v.number_of_comments, "\
            "t.number_of_reactions = v.number_of_reactions, "\
            "t.number_of_views = v.number_of_views, "\
            "t.updated_at = v.updated_at "

        sql = ""\
            f"UPDATE tbl_messages AS t " \
            f"JOIN ({sql_join_select}) AS v " \
            f"ON {sql_on} " \
            f"SET {sql_set};"

        if isSecondDB:
            connection = mysql.new_connection_second_db()
        else:
            connection = mysql.new_connection()

        cursor = connection.cursor()

        cursor.execute(sql, flat_data)

        connection.commit()
        cursor.close()
        connection.close()

    except Exception as e:
        err_message = f"error transaction.update_data_to_mysql()\n\n {e}"

        print(err_message)
        telegram_notify.send_to_private(message=err_message)


async def insert_post_and_comments_data_to_mysql(new_data=[], isSecondDB=False):
    insert_len = 0
    update_len = 0

    try:
        if len(new_data) == 0:
            return None

        data_insert, data_update = await classify_insert_or_update_data(new_data, isSecondDB=isSecondDB)

        await insert_data_to_mysql(data_insert, isSecondDB=isSecondDB)
        await update_data_to_mysql(data_update, isSecondDB=isSecondDB)

        insert_len = len(data_insert)
        update_len = len(data_update)
    except Exception as e:
        err_message = f"error transaction.insert_post_and_comments_data_to_mysql()\n\n {'Error In second db' if isSecondDB else ''} \n\n {e}"

        print(err_message)
        telegram_notify.send_to_private(message=err_message)

    return insert_len, update_len


async def pushTransactionScrapingResult(keyword_id="", source_id="", number_of_result=0, organization_id=None, flag_error=""):
    # return None
    try:
        db_connection = mysql.new_connection()
        db_cursor = db_connection.cursor()

        now = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

        try:
            sql_post_ct = "INSERT INTO crw_transactions (activity_at, keyword_id, source_id, craw_result, number_of_result, remark,flag_error) values(%s, %s, %s, %s, %s, %s, %s)"
            val_post_ct = (now, keyword_id, source_id,
                           "success", number_of_result, "", flag_error)
            db_cursor.execute(sql_post_ct, val_post_ct)

        except Exception as e:
            lineNotify.send_notify_scraping_result(
                f"MySql พบข้อผิดพลาดในการเพิ่มข้อมูลไปที่ crw_transactions\n\n{e}")

        try:
            # sql_put_ckc = "UPDATE crw_keyword_craws SET last_crawed_at = %s, number_of_result = number_of_result + %s WHERE keyword_id = %s AND source_id = %s"
            sql_put_ckc = "UPDATE crw_keyword_craws SET number_of_result = number_of_result + %s WHERE keyword_id = %s AND source_id = %s"
            val_put_ckc = (number_of_result, keyword_id, source_id)
            db_cursor.execute(sql_put_ckc, val_put_ckc)

        except Exception as e:
            lineNotify.send_notify_scraping_result(
                f"MySql พบข้อผิดพลาดในการอัพเดทข้อมูลไปที่ crw_keyword_craws\n\n{e}")

        try:
            if organization_id is not None:
                number_of_result_double = number_of_result * 2

                sql_put_org = "UPDATE tbl_organizations SET transaction_reamining = transaction_reamining - %s WHERE id = %s"
                val_put_org = (number_of_result_double, organization_id)
                db_cursor.execute(sql_put_org, val_put_org)

        except Exception as e:
            lineNotify.send_notify_scraping_result(
                f"MySql พบข้อผิดพลาดในการอัพเดทข้อมูลไปที่ tbl_organizations\n\n{e}")

        db_connection.commit()
    except Exception as e:
        lineNotify.send_notify_to_dev(
            f"WARNING [service/transaction] pushTransactionScrapingResult : \n\n{e}.")


async def save_last_craw_at(keyword_id="", source_id=""):
    try:
        db_connection = mysql.new_connection()
        db_cursor = db_connection.cursor()

        now = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

        sql = "UPDATE crw_keyword_craws SET last_crawed_at = %s WHERE keyword_id = %s AND source_id = %s"
        value = (now, keyword_id, source_id)
        db_cursor.execute(sql, value)

        db_connection.commit()
    except Exception as e:
        telegram_notify.send_to_private(
            message=f"error transaction.save_last_craw_at()\n\n {e}")


# async def updatePostsAndCommentsData(data=[], collection_name="", campaign_id="", keyword_id=""):
#     result = None

#     try:
#         collection_name = f"{collection_name}_{campaign_id}_{keyword_id}"
#         ___collection = mongo.get_db_driver()[collection_name]

#         now_time_string = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#         bulk_operations = [
#             UpdateOne(
#                 {
#                     'full_text': doc['full_text'],
#                 },
#                 {
#                     '$set': {**doc, "last_update": now_time_string},
#                     '$setOnInsert': {"scraping_at": now_time_string},
#                 },
#                 upsert=True,
#             ) for doc in data
#         ]
#         result = ___collection.bulk_write(bulk_operations, ordered=False)

#         # for d in data:
#         # d["scraping_at"] = now_time_string

#         # result = ___collection.insert_many(data)

#     except Exception as e:
#         if "Connection refused" in f"{e}":
#             lineNotify.send_notify_scraping_result(
#                 message=f"\n{collection_name}:\n\n รอการเชื่อมต่อ MongoDB")
#         else:
#             lineNotify.send_to_scraper_problem(
#                 message=f"\n{collection_name}:\n\nerror in connection mongodb {e}")

#         result = None

#     return result


# async def updatePostsAndCommentsDataInstagram(data=[], campaign_id="", keyword_id=""):
#     result = None

#     try:
#         collection_name = f"{collection_name_instagram}_{campaign_id}_{keyword_id}"
#         ___collection = mongo.get_db_driver()[collection_name]

#         now_time_string = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#         for d in data:
#             d["scraping_at"] = now_time_string

#         result = ___collection.insert_many(data)

#     except Exception as e:
#         if "Connection refused" in f"{e}":
#             message = f"\n{collection_name}:\n\n รอการเชื่อมต่อ MongoDB"
#             lineNotify.send_notify_scraping_result(message)
#         else:
#             message = f"\n{collection_name}:\n\nerror in connection mongodb {e}"
#             lineNotify.send_to_scraper_problem(message)

#         result = None

#     return result
