
import db.mysql_test as mysql


async def getActiveKeyword():
    result = []
    try:
        db_connection = mysql.new_connection()
        db_cursor = db_connection.cursor()

        sql_query = (
            "SELECT "
            + "tk.id,tk.name,tk.campaign_id,tk.keyword_or,tk.keyword_and,tk.keyword_exclude,tk.status,"
            + "tc.name as campaign_name,tc.organization_id,tc.start_at,tc.end_at,tc.frequency,"
            + "toz.transaction_limit,toz.transaction_reamining "

            + "FROM tbl_keywords as tk "
            + "LEFT JOIN tbl_campaigns as tc "
            + "ON tk.campaign_id = tc.id "
            + "LEFT JOIN tbl_organizations as toz "
            + "ON tc.organization_id = toz.id "

            + "WHERE tk.status = 1;"
        )
        db_cursor.execute(sql_query)
        for row in db_cursor.fetchall():
            result.append({
                "id": row[0],
                "name": row[1],
                "campaign_id": row[2],
                "keyword_or": row[3],
                "keyword_and": row[4],
                "keyword_exclude": row[5],
                "status": row[6],
                "campaign_name": row[7] if row[7] is not None else "null",
                "organization_id": row[8],
                "start_at": row[9],
                "end_at": row[10],
                "frequency": row[11],
                "transaction_limit": row[12],
                "transaction_reamining": row[13],
            })

        db_cursor.close()

    except Exception as e:
        print(
            f"WARING SQL [getActiveKeyword]: {e}.")

    return result


async def get_last_craw_date(keyword_id=0, source_id=0):
    result = []
    try:
        db_connection = mysql.new_connection()
        db_cursor = db_connection.cursor()

        sql_query = (
            "SELECT id,last_crawed_at "
            + "FROM crw_keyword_craws "
            + "WHERE keyword_id = %s AND source_id = %s LIMIT 1;"
        )
        db_cursor.execute(sql_query, (keyword_id, source_id))

        for row in db_cursor.fetchall():
            result.append({
                "id": row[0],
                "last_crawed_at": row[1],
            })

        db_cursor.close()

    except Exception as e:
        print(
            f"WARING SQL [get_last_craw_date]: {e}.")

    return result[0]['last_crawed_at'] if len(result) > 0 else None
