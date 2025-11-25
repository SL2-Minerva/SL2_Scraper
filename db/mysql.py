import mysql.connector
import envconstant.env as env


def new_connection():
    __connection = mysql.connector.connect(
        host=env.MYSQL_HOST,
        port=env.MYSQL_PORT,
        user=env.MYSQL_USERNAME,
        password=env.MYSQL_PASSWORD,
        database=env.MYSQL_DB_NAME
    )
    return __connection
