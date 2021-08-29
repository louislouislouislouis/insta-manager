import datetime


class User:
    def __init__(self, username, full_name=None, insta_id=None, followers=[], followings=[], bio=None):
        self.username = username
        self.full_name = full_name
        self.insta_id = insta_id
        self.followers = followers
        self.followings = followings
        self.collection_name = "insta_manager__user"
        self.bio = bio

    def get_mongo_obj(self):
        return {
            "username": self.username,
            "full_name": self.full_name,
            "insta_id": self.insta_id,
            "followers": self.followers,
            "followings": self.followings,
            "bio": self.bio,
            "last_modified": datetime.datetime.utcnow()
        }

    def find_user_by_insta_id(self, database):
        collection = database[self.collection_name]
        user = collection.find_one({"insta_id": self.insta_id})
        return user

    def find_user_by_username(self, database):
        collection = database[self.collection_name]
        user = collection.find_one({"username": self.username})
        return user

    def save_user(self, database):
        # if we need to update
        if self.find_user_by_username(database):
            # get the element to modify
            my_query = {"username": self.username}
            # change value
            new_values = {"$set": self.get_mongo_obj()}
            # get collection and update
            collection = database[self.collection_name]
            collection.update_one(my_query, new_values)
            return "The information about " + self.username + " has been updated in database"
        if self.find_user_by_insta_id(database):
            # get the element to modify
            my_query = {"insta_id": self.insta_id}
            # change value
            new_values = {"$set": self.get_mongo_obj()}
            # get collection and update
            collection = database[self.collection_name]
            collection.update_one(my_query, new_values)
            return "The information about" + self.username + "has been updated in database"

        # if we need to add
        collection = database[self.collection_name]
        collection.insert_one(self.get_mongo_obj())
        return "The information about" + self.username + "has been added to database"
