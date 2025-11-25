import mysql.connector

__connection = mysql.connector.connect(
    host="localhost",
    port="3307",
    user="root",
    password="1234",
    database="sl_keyword"
)


def get_db_connection():
    return __connection


def close_db_connection():
    __connection.close()
