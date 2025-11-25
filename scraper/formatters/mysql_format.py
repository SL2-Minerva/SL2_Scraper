from datetime import datetime


def format_value_mysql(
    message_id, reference_message_id, keyword_id, message_datetime, author,
    source_id, full_message, link_message, link_image, link_profile_image, message_type,
    media_type, number_of_shares, number_of_comments, number_of_reactions, number_of_views
):

    return (message_id, reference_message_id, keyword_id, message_datetime, author,
            source_id, full_message, link_message, link_image, link_profile_image, message_type,
            media_type, number_of_shares, number_of_comments, number_of_reactions, number_of_views, datetime.now(), datetime.now())


def get_insert_sql_message(values):
    return "INSERT INTO tbl_messages (" \
        "message_id, reference_message_id, keyword_id, message_datetime, author," \
        " source_id, full_message, link_message, link_image, link_profile_image, message_type," \
        " media_type, number_of_shares, number_of_comments, number_of_reactions, number_of_views," \
        f" created_at, updated_at) VALUES {values}"
