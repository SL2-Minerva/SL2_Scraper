

import db.mysql as mysql

from modules import telegram_notify

platform_x = "x"
platform_twitter = "twitter"
platform_tiktok = "tiktok"
platform_pantip = "pantip"
platform_facebook = "facebook"
platform_youtube = "youtube"
platform_instagram = "instagram"


async def getActiveKeyword(platform=None):
    result = []

    if platform is None or platform == "":
        return result

    sql_where_platform = ""

    if platform == platform_x or platform == platform_twitter:
        sql_where_platform = f"AND (tbl_campaigns.platform LIKE '%{platform_x}%' OR tbl_campaigns.platform LIKE '%{platform_twitter}%')"
    else:
        sql_where_platform = f"AND tbl_campaigns.platform LIKE '%{platform}%'"

    try:
        db_connection = mysql.new_connection()
        db_cursor = db_connection.cursor()

        sql_query = (
            "SELECT "
            + "tbl_keywords.id,tbl_keywords.name,tbl_keywords.campaign_id,"
            + "tbl_keywords.keyword_or,tbl_keywords.keyword_and,tbl_keywords.keyword_exclude,tbl_keywords.status,"
            + "tbl_campaigns.name as campaign_name,tbl_campaigns.organization_id,"
            + "tbl_campaigns.start_at,tbl_campaigns.end_at,tbl_campaigns.frequency,"
            + "tbl_organizations.transaction_limit,tbl_organizations.transaction_reamining,tbl_campaigns.platform "

            + "FROM tbl_keywords "

            + "LEFT JOIN tbl_campaigns "
            + "ON tbl_keywords.campaign_id = tbl_campaigns.id "

            + "LEFT JOIN tbl_organizations "
            + "ON tbl_campaigns.organization_id = tbl_organizations.id "

            + f"WHERE tbl_keywords.status = 1 {sql_where_platform};"
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
        telegram_notify.send_to_scraper_notify(
            message=f"การดึงข้อมูล Keywords จาก MySQL ขัดข้อง\n\n {e}.")

    return result


async def get_last_craw_date(keyword_id=0, source_id=0):
    try:
        result = []

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

        if len(result) > 0:
            return result[0]['last_crawed_at']

    except Exception as e:
        telegram_notify.send_to_scraper_notify(
            message=f"การดึงข้อมูล last_crawed_at จาก MySQL ขัดข้อง\n\n {e}.")

    return None
