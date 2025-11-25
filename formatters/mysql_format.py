from datetime import datetime


def format_value_mysql(
    message_id, reference_message_id, keyword_id, message_datetime, author,
    source_id, full_message, link_message, link_image, link_video, link_profile_image, message_type,
    media_type, number_of_shares, number_of_comments, number_of_reactions, number_of_views
):
    reference_message_id = reference_message_id if reference_message_id is not None else "NULL"
    # link_image = link_image if link_image is not None and link_image != "" else "NULL"
    # link_video = link_video if link_video is not None and link_video != "" else "NULL"
    # link_profile_image = link_profile_image if link_profile_image is not None and link_profile_image != "" else "NULL"

    return (message_id, reference_message_id, keyword_id, message_datetime, author,
            source_id, full_message, link_message, link_image, link_video, link_profile_image, message_type,
            media_type, number_of_shares, number_of_comments, number_of_reactions, number_of_views, datetime.now(), datetime.now())


# TODO: if you change the number of fields, make sure to update fn "insert_data_to_mysql" to change count %s%


def get_insert_sql_message(values):
    return "INSERT INTO tbl_messages (" \
        "message_id, reference_message_id, keyword_id, message_datetime, author," \
        " source_id, full_message, link_message, link_image, link_video, link_profile_image, message_type," \
        " media_type, number_of_shares, number_of_comments, number_of_reactions, number_of_views," \
        f" created_at, updated_at) VALUES {values}"
