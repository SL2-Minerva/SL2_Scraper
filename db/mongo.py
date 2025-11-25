from pymongo import MongoClient
from bson import ObjectId

import envconstant.env as env

#url = f"mongodb://{env.MONGO_USERNAME}:{env.MONGO_PASSWORD}@{env.MONGO_HOST}:{env.MONGO_PORT}/?authenticationDatabase={env.MONGO_DB_NAME}"
url = f"mongodb://{env.MONGO_USERNAME}:{env.MONGO_PASSWORD}@{env.MONGO_HOST}:{env.MONGO_PORT}/{env.MONGO_DB_NAME}"

client = MongoClient(url)
__db = client[env.MONGO_DB_NAME]


def get_db_driver():
    return __db


def json_serial(obj):
    """JSON serializer for objects not serializable by default JSON encoder."""
    if isinstance(obj, ObjectId):
        return str(obj)

    raise TypeError("Type not serializable")
