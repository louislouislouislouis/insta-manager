import datetime
from instaManager.exception import *


class User:
    def __init__(self, username, full_name=None, insta_id=None, followers=[], followings=[], bio=None,
                 last_modified=None):
        self.username = username
        self.full_name = full_name
        self.insta_id = insta_id
        self.followers = followers
        self.followings = followings
        self.collection_name = "insta_manager__user"
        self.bio = bio
        self.last_modified = last_modified

    def get_mongo_obj(self):
        # verif data
        if not isinstance(self.username, str):
            raise BadUserSyntaxError.BadUserSyntaxError()
        if not isinstance(self.full_name, str):
            raise BadUserSyntaxError.BadUserSyntaxError()
        if not isinstance(self.insta_id, str):
            raise BadUserSyntaxError.BadUserSyntaxError()
        if not isinstance(self.bio, str):
            raise BadUserSyntaxError.BadUserSyntaxError()
        for follower in self.followers:
            if not isinstance(follower["username"], str):
                raise BadUserSyntaxError.BadUserSyntaxError()
            if not isinstance(follower["insta_id"], str):
                raise BadUserSyntaxError.BadUserSyntaxError()
        for following in self.followings:
            if not isinstance(following["username"], str):
                raise BadUserSyntaxError.BadUserSyntaxError()
            if not isinstance(following["insta_id"], str):
                raise BadUserSyntaxError.BadUserSyntaxError()

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
        if user:
            return User(user["username"], user["full_name"], user["insta_id"], user["followers"], user["followings"],
                        user["bio"], user["last_modified"])
        return user

    def find_user_by_username(self, database):
        collection = database[self.collection_name]
        user = collection.find_one({"username": self.username})
        if user:
            return User(user["username"], user["full_name"], user["insta_id"], user["followers"], user["followings"],
                        user["bio"], user["last_modified"])
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
        return "The information about" + self.username + " has been added to database"
