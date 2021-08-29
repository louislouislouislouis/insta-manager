from pymongo import MongoClient, errors
from instaManager.exception import *


class MongoManager:
    def __init__(self, db_name, user, password, host="127.0.0.1", port=27017, server_selection_timeout_ms=2000):
        self.db_user = user
        self.db_pw = password
        self.db_host = host
        self.db_port = port
        self.db_name = db_name
        url = "mongodb://" + self.db_user + ":" + self.db_pw + "@" + self.db_host + ":" + str(
            self.db_port) + "/"
        self.client = MongoClient(url, serverSelectionTimeoutMS=server_selection_timeout_ms)
        self.database = self.client[self.db_name]
        try:
            self.client.server_info()
        except errors.OperationFailure as bad_except:
            raise NoDatabaseError.NoDatabaseError(bad_except.details)
        except errors.ServerSelectionTimeoutError as bad_except:
            print(bad_except)
            raise NoDatabaseError.NoDatabaseError({"codeName": "Timeout Exception"})
