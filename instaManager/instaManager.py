# sys import
import json
import sys
import os
import re
import time
import random
import urllib

# selenium libraries
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
# plot
import numpy as np
import matplotlib as mpl

# data viz
from pyvis.network import Network

# custom exception
from instaManager.exception import *

# custom interaction
from instaManager.interaction.interaction import click
from instaManager.interaction.interaction import get
from instaManager.interaction.interaction import send_keys

# custom log
from instaManager.logger.log import Log

# custom db manager
from instaManager.mongoManager.mongoManager import MongoManager

# custom python model
from instaManager.model.user import User

# const
XPATH_FILENAME = os.path.join(os.path.dirname(__file__), 'config/xpath.json')
URL_FILENAME = os.path.join(os.path.dirname(__file__), 'config/url.json')
DB_CREDENTIALS_FILENAME = os.path.join(os.path.dirname(__file__), 'config/credentials_db.json')
COMMENTS_FILENAME = os.path.join(os.path.dirname(__file__), 'data/comments.json')
HASHTAGS_FILENAME = os.path.join(os.path.dirname(__file__), 'data/hashtags.json')


class InstaManager:
    def __init__(self, path_to_driver, username, password, private=True, headless=False):

        self.username = username
        self.password = password
        self.is_connected = False
        self.logger = Log("INSTAMANAGER")
        self.headless = headless
        self.db_client = None

        # database manager
        try:
            f = open(DB_CREDENTIALS_FILENAME)
            cred = json.load(f)
            self.db_client = MongoManager(cred["name"], cred["login"], cred["pw"])
            self.logger.print("Database found", color="blue", method="CONSTRUCTOR")
        except NoDatabaseError.NoDatabaseError as bad_except:
            self.db_client = None
            self.logger.print("Error while initialized database: " + bad_except.json["codeName"], color="yellow",
                              method="CONSTRUCTOR")
        except KeyError as bad_except:
            self.db_client = None
            self.logger.print("Error while initialized database: cannot find key: `" + str(
                bad_except) + "` in " + DB_CREDENTIALS_FILENAME,
                              color="yellow",
                              method="CONSTRUCTOR")
        except FileNotFoundError:
            self.db_client = None
            self.logger.print("Error while initialized database: cannot find file: `" + DB_CREDENTIALS_FILENAME,
                              color="yellow",
                              method="CONSTRUCTOR")

        # get json data
        try:
            f = open(XPATH_FILENAME)
            self.xpath = json.load(f)
        except Exception as bad_except:
            print(bad_except)
            raise XPathNotFoundError.XPathNotFoundError()
            sys.exit()
        try:
            f = open(URL_FILENAME)
            self.urls = json.load(f)
        except Exception as bad_except:
            print(bad_except)
            raise UrlNotFoundError.UrlNotFoundError()
            sys.exit()

        # create driver
        chrome_options = webdriver.ChromeOptions()
        if private:
            chrome_options.add_argument("--incognito")
            if self.headless:
                chrome_options.add_argument("--window-size=1920,1080")
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument(
                    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")

        self.driver = webdriver.Chrome(path_to_driver, options=chrome_options)
        self.logger.print("Class InstaManager initialized", color="blue", method="CONSTRUCTOR")

    def connect(self, max_time=6):
        try:
            self.logger.print("Trying to connect...", color="blue", method="CONNECT")
            # get into connect page
            get(self.driver, self.urls.get("connecting_page"))
            # accept cookie
            click(self.driver, self.xpath.get("connecting_page").get("cookie_accept_button"), max_time)
            # enter login and password
            send_keys(self.driver, self.xpath.get("connecting_page").get("login_input"), self.username, max_time)
            send_keys(self.driver, self.xpath.get("connecting_page").get("password_input"), self.password, max_time)
            # click connect button
            click(self.driver, self.xpath.get("connecting_page").get("submit_button_login"), max_time)
            # not save infos and notification
            click(self.driver, self.xpath.get("homepage").get("not_save_id_button"), max_time)
            click(self.driver, self.xpath.get("homepage").get("not_notify_button"), )
            self.is_connected = True
            self.logger.print("Connecting successful...", color="blue", method="CONNECT")
        except TimeoutException as bad_except:
            elem = self.driver.find_element_by_xpath("//*")
            source_code = elem.get_attribute("outerHTML")
            print(source_code)
            self.logger.print("Trouble connecting in insta", type="ERROR", color="red", method="CONNECT")
            self.logger.print(bad_except, "ERROR", color="red", method="CONNECT")

    def find_and_comment_post_by_tag(self, tags, percentage_like=0.5, percentage_comment=0.5, sleep_time=20,
                                     limits_like=20, limits_comments=20):
        self.logger.print("Start comment and like by tag session", color="blue", method="FIND AND INTERACT BY TAGS")
        if not self.is_connected:
            raise NotConnectedError.NotConnectedError()
        else:
            stats = {"comments": 0, "likes": 0}
            # find comments
            try:
                f = open(COMMENTS_FILENAME)
                comments = json.load(f)
            except Exception as bad_except:
                print(bad_except)
                raise CommentsNotFoundError.CommentsNotFoundError()
                sys.exit()

            # find relative hashtags
            try:
                f = open(HASHTAGS_FILENAME)
                json_hash = json.load(f)
                if json_hash.get(tags) is None:
                    relative_hash = []
                else:
                    relative_hash = json_hash.get(tags).get("relative_tags")
            except Exception as bad_except:
                print(bad_except)
                raise HashTagsNotFoundError.HashTagsNotFoundError()
                sys.exit()

            # get a list of post to interact
            post_ids = []
            url = re.sub("\{.*?\}", tags, self.urls.get("post_by_tag"))
            get(self.driver, url)
            content = self.driver.find_element_by_tag_name('pre').text
            parsed_json = json.loads(content)
            for section in parsed_json["data"]["recent"]["sections"]:
                for media in section["layout_content"]["medias"]:
                    if media["media"]["caption"] and media["media"]["caption"]["text"]:
                        hashtags = re.findall("[#]\w+", media["media"]["caption"]["text"])
                    else:
                        hashtags = []
                    level = 1
                    for hashtag in hashtags:
                        real_hashtags = hashtag[1:].lower()
                        if real_hashtags in relative_hash:
                            level += 1

                    post_ids.append(
                        {"level": level, "type": media["media"]["media_type"],
                         "user": media["media"]["user"]["username"],
                         "post_id": media["media"]["code"]})

            # interact with posts
            for post_id in post_ids:

                # get into post page
                url = re.sub("\{.*?\}", post_id["post_id"], self.urls.get("post_by_id"))
                get(self.driver, url)
                # focus on text area
                click(self.driver, self.xpath.get("post_page").get("comment_text_area"))

                # comment conditional
                if random.random() < percentage_comment * post_id["level"] and stats.get("comments") < limits_comments:
                    if post_id["type"] == 2:
                        # get random video comment
                        comment = comments["default"]["video"][random.randint(0, len(comments["default"]["video"]) - 1)]
                    else:
                        # get random picture comment
                        comment = comments["default"]["picture"][
                            random.randint(0, len(comments["default"]["picture"]) - 1)]
                    # replace dynamic id in comment
                    comment = re.sub("\{.*?\}", post_id["user"], comment)
                    # do comment
                    send_keys(self.driver, self.xpath.get("post_page").get("comment_text_area"), comment)
                    time.sleep(0.5)
                    # publish comment
                    click(self.driver, self.xpath.get("post_page").get("publish_comment_button"), )
                    # stats
                    stats["comments"] += 1
                    self.logger.print("Just comment a level " + str(post_id["level"]) + " post", color="blue",
                                      method="FIND AND INTERACT BY TAGS")

                # like conditional
                if random.random() < percentage_like * post_id["level"] and stats.get("likes") < limits_like:
                    click(self.driver, self.xpath.get("post_page").get("like_button"), )
                    # stats
                    stats["likes"] += 1
                    self.logger.print("Just lik a level " + str(post_id["level"]) + " post", color="blue",
                                      method="FIND AND INTERACT BY TAGS")

                if stats["comments"] == limits_comments and stats["likes"] == limits_like:
                    self.logger.print("Max interaction reached", color="blue", method="FIND AND INTERACT BY TAGS")
                    break

                self.logger.print(
                    "Just finish interacting a post of level " + str(post_id["level"]) + " // Stats: " + str(stats),
                    color="blue", method="FIND AND INTERACT BY TAGS")
                # sleep before next iteration
                time.sleep(sleep_time)
            self.logger.print("Finish comment and like by tag session", color="blue",
                              method="FIND AND INTERACT BY TAGS")
            return stats

    def get_user_data(self, username):
        # get profile url
        url = re.sub("\{.*?\}", username, self.urls.get("profile_page"))
        # json format
        url += "/?__a=1"
        # load browser
        get(self.driver, url)
        # get good data
        content = self.driver.find_element_by_tag_name('pre').text
        parsed_json = json.loads(content)
        # get beginning of user data
        real_user_id = parsed_json.get("graphql").get("user").get("id")
        full_user_name = parsed_json.get("graphql").get("user").get("full_name")
        user_bio = parsed_json.get("graphql").get("user").get("biography")

        # loop for followers
        has_next = True
        after = None
        followers = {}
        followings = {}
        followers_array = []
        followings_array = []
        while has_next:
            params = {"id": real_user_id,
                      "include_reel": True,
                      "fetch_mutual": True,
                      "first": 50,
                      "after": after
                      }
            params = urllib.parse.quote_plus(json.dumps(params).replace(' ', ""))

            url = self.urls.get("graphql_query").replace("{QUERY_HASH}", "c76146de99bb02f6415203be841dd25a").replace(
                "{VAR_VAL}", params)
            get(self.driver, url)
            # get data
            content = self.driver.find_element_by_tag_name('pre').text
            parsed_json = json.loads(content)
            if parsed_json.get("status") != "ok":
                raise GraphQLError.GraphQLError(parsed_json)
            has_next = parsed_json.get("data").get("user").get("edge_followed_by").get("page_info").get("has_next_page")
            after = parsed_json.get("data").get("user").get("edge_followed_by").get("page_info").get("end_cursor")
            followers_raw = parsed_json.get("data").get("user").get("edge_followed_by").get("edges")
            for follower_raw in followers_raw:
                user_name = follower_raw.get("node").get("username")
                full_name = follower_raw.get("node").get("full_name")
                followers_array.append({"insta_id": follower_raw.get("node").get("id"), "username": user_name})
                followers[follower_raw.get("node").get("id")] = {"username": user_name, "full_name": full_name}
            time.sleep(1)

        # loop for followings
        has_next = True
        after = None
        while has_next:
            params = {"id": real_user_id,
                      "include_reel": True,
                      "fetch_mutual": True,
                      "first": 50,
                      "after": after
                      }
            params = urllib.parse.quote_plus(json.dumps(params).replace(' ', ""))
            url = self.urls.get("graphql_query").replace("{QUERY_HASH}",
                                                         "d04b0a864b4b54837c0d870b0e77e076").replace(
                "{VAR_VAL}", params)

            get(self.driver, url)
            # get data
            content = self.driver.find_element_by_tag_name('pre').text
            parsed_json = json.loads(content)
            if parsed_json.get("status") != "ok":
                raise GraphQLError.GraphQLError(parsed_json)
            has_next = parsed_json.get("data").get("user").get("edge_follow").get("page_info").get(
                "has_next_page")
            after = parsed_json.get("data").get("user").get("edge_follow").get("page_info").get(
                "end_cursor")
            followings_raw = parsed_json.get("data").get("user").get("edge_follow").get("edges")

            for following_raw in followings_raw:
                user_name = following_raw.get("node").get("username")
                full_name = following_raw.get("node").get("full_name")
                followings_array.append({"insta_id": following_raw.get("node").get("id"), "username": user_name})
                followings[following_raw.get("node").get("id")] = {"username": user_name, "full_name": full_name}
            time.sleep(1)

        # create user
        new_user = User(username, full_user_name, real_user_id, followers_array, followings_array, user_bio)
        # database
        if self.db_client:
            infos = new_user.save_user(self.db_client.database)
            self.logger.print(infos, color="blue", method="GET USER DATA")

        return new_user
        # treat data - common friends
        mutual_friendship = followings.keys() & followers.keys()
        mutual_friends = {}
        for inter in mutual_friendship:
            mutual_friends[inter] = followers[inter]

        # treat data - fake friends
        fake_friends_not_follow_by_me = {}
        fake_friends_not_following_me = {}
        for i in followers:
            if i not in mutual_friendship:
                fake_friends_not_follow_by_me[i] = followers[i]
        for i in followings:
            if i not in mutual_friendship:
                fake_friends_not_following_me[i] = followings[i]

        return mutual_friends, fake_friends_not_follow_by_me, fake_friends_not_following_me

    def get_real_friends(self, username, optimized=False):
        # get data of user
        if optimized and self.db_client:
            self.logger.print("Optimized version detected", color="blue", method="GET REAL FRIENDS")
            short_user = User(username)
            user = short_user.find_user_by_username(self.db_client.database)
            if not user:
                self.logger.print("Cannot find " + username + " in db", color="yellow", method="GET REAL FRIENDS")
                try:
                    user = self.get_user_data(username)
                    optimized_result = False
                except GraphQLError.GraphQLError as bad_except:
                    raise bad_except
            else:
                self.logger.print("Find " + username + " in db. Data from " + str(user.last_modified), color="blue",
                                  method="GET REAL FRIENDS")
                optimized_result = True
        else:
            try:
                user = self.get_user_data(username)
                optimized_result = False
            except GraphQLError.GraphQLError as bad_except:
                raise bad_except

        # calc real friends
        dict_user_followers = {follower["insta_id"]: follower["username"] for follower in user.followers}
        dict_user_followings = {following["insta_id"]: following["insta_id"] for following in user.followings}
        real_friends_user_keys = dict_user_followers.keys() & dict_user_followings.keys()
        real_friends_user = {}
        for inter in real_friends_user_keys:
            real_friends_user[inter] = dict_user_followers[inter]
        return real_friends_user, optimized_result

    def get_friendship_status(self, username_1, username_2, optimized=False):
        # get user 1 friends
        try:
            real_friends_user_1, optimized_result = self.get_real_friends(username_1, optimized)
        except GraphQLError.GraphQLError as bad_except:
            if "patienter" in bad_except.json.get("message"):
                self.logger.print("Limits of request reached, sleep 120", color="yellow",
                                  method="GET FRIENDSHIP STATUS")
                time.sleep(120)
                try:
                    real_friends_user_1, optimized_result = self.get_real_friends(username_1, optimized)
                except GraphQLError.GraphQLError:
                    self.logger.print("Limits of request reached, impossible to go further", color="red",
                                      method="GET FRIENDSHIP STATUS")
                    return
            elif "limited" in bad_except.json.get("message"):
                self.logger.print("Too many request done, sleep 240", color="red", method="GET FRIENDSHIP STATUS")
                time.sleep(240)
                try:
                    real_friends_user_1, optimized_result = self.get_real_friends(username_1, optimized)
                except GraphQLError.GraphQLError:
                    self.logger.print("Limits of request reached, impossible to go further", color="red",
                                      method="GET FRIENDSHIP STATUS")
                    return

        # get user 2 friends
        try:
            real_friends_user_2, optimized_result = self.get_real_friends(username_2, optimized)
        except GraphQLError.GraphQLError as bad_except:
            if "patienter" in bad_except.json.get("message"):
                self.logger.print("Limits of request reached, sleep 120", color="yellow",
                                  method="GET FRIENDSHIP STATUS")
                time.sleep(120)
                try:
                    real_friends_user_2, optimized_result = self.get_real_friends(username_2, optimized)
                except GraphQLError.GraphQLError:
                    self.logger.print("Limits of request reached, impossible to go further", color="red",
                                      method="GET FRIENDSHIP STATUS")
                    return
            elif "limited" in bad_except.json.get("message"):
                self.logger.print("Too many request done, sleep 240", color="red", method="GET FRIENDSHIP STATUS")
                time.sleep(240)
                try:
                    real_friends_user_2, optimized_result = self.get_real_friends(username_2, optimized)
                except GraphQLError.GraphQLError:
                    self.logger.print("Limits of request reached, impossible to go further", color="red",
                                      method="GET FRIENDSHIP STATUS")
                    return

        real_common_friends = real_friends_user_2.keys() & real_friends_user_1.keys()
        string1 = username_2 + " and " + username_1 + " have " + str(len(real_common_friends)) + " friends in common"
        string2 = str((len(real_common_friends) / len(
            real_friends_user_1)) * 100) + "% of " + username_1 + "'s friends are friends with " + username_2
        string3 = str((len(real_common_friends) / len(
            real_friends_user_2)) * 100) + "% of " + username_2 + "'s friends are friends with " + username_1
        self.logger.print(string1, color="green", method="GET FRIENDSHIP STATUS")
        self.logger.print(string2, color="green", method="GET FRIENDSHIP STATUS")
        self.logger.print(string3, color="green", method="GET FRIENDSHIP STATUS")

        return real_common_friends

    def get_all_friendship_status(self):
        if not self.is_connected:
            raise NotConnectedError.NotConnectedError()
        try:
            real_friends, optimized_result = self.get_real_friends(self.username, optimized=True)
        except GraphQLError.GraphQLError as bad_except:
            if "patienter" in bad_except.json.get("message"):
                self.logger.print("Limits of request reached, sleep 120", color="yellow",
                                  method="GET FRIENDSHIP STATUS")
                time.sleep(300)
                try:
                    real_friends, optimized_result = self.get_real_friends(self.username, optimized=True)
                except GraphQLError.GraphQLError:
                    self.logger.print("Limits of request reached, impossible to go further", color="red",
                                      method="GET FRIENDSHIP STATUS")
                    return
            elif "limited" in bad_except.json.get("message"):
                self.logger.print("Too many request done, sleep 240", color="red", method="GET FRIENDSHIP STATUS")
                return
                time.sleep(240)
                try:
                    real_friends, optimized_result = self.get_real_friends(self.username, optimized=True)
                except GraphQLError.GraphQLError:
                    self.logger.print("Limits of request reached, impossible to go further", color="red",
                                      method="GET FRIENDSHIP STATUS")
                    return

        result = {}
        all_data = {}

        for friends in real_friends:
            try:
                mutual_friends_of_friends, optimized_result = self.get_real_friends(real_friends.get(friends),
                                                                                    optimized=True)
                all_data[friends] = mutual_friends_of_friends
            except GraphQLError.GraphQLError as bad_except:
                if "patienter" in bad_except.json.get("message"):
                    self.logger.print("Limits of request reached, sleep 120", color="yellow",
                                      method="GET FRIENDSHIP STATUS")
                    time.sleep(300)
                    try:
                        mutual_friends_of_friends, optimized_result = self.get_real_friends(real_friends.get(friends),
                                                                                            optimized=True)
                        all_data[friends] = mutual_friends_of_friends
                    except GraphQLError.GraphQLError:
                        self.logger.print("Limits of request reached, impossible to go further", color="red",
                                          method="GET FRIENDSHIP STATUS")
                        return
                elif "limited" in bad_except.json.get("message"):
                    self.logger.print("Too many request done, sleep 240", color="red", method="GET FRIENDSHIP STATUS")
                    return
                    ime.sleep(240)
                    try:
                        mutual_friends_of_friends, optimized_result = self.get_real_friends(real_friends.get(friends),
                                                                                            optimized=True)
                        all_data[friends] = mutual_friends_of_friends
                    except GraphQLError.GraphQLError:
                        self.logger.print("Limits of request reached, impossible to go further", color="red",
                                          method="GET FRIENDSHIP STATUS")
                        return

            mutual_friendship = real_friends.keys() & mutual_friends_of_friends.keys()
            try:
                result[real_friends.get(friends)] = {
                    "id": friends,
                    "same_real_friends_number": len(mutual_friendship),
                    "percentage_real_friends_common": (len(mutual_friendship) / len(mutual_friends_of_friends)) * 100}
            except ZeroDivisionError:
                self.logger.print("length of common friends equal to 0", color="blue", method="GET FRIENDSHIP STATUS")
                result[real_friends.get(friends)] = {
                    "id": friends,
                    "same_real_friends_number": len(mutual_friendship),
                    "percentage_real_friends_common": 0}
            if not optimized_result:
                time.sleep(45)

        sorted_friends_by_percentage = sorted(result.items(), key=lambda x: x[1].get("percentage_real_friends_common"),
                                              reverse=True)
        for i in range(len(sorted_friends_by_percentage)):
            print(str(i + 1) + ": " + str(sorted_friends_by_percentage[i][0]) + "-->" + str(
                sorted_friends_by_percentage[i][1]))
        print("")
        sorted_friends_by_number = sorted(result.items(), key=lambda x: x[1].get("same_real_friends_number"),
                                          reverse=True)
        for i in range(len(sorted_friends_by_number)):
            print(str(i + 1) + ": " + str(sorted_friends_by_number[i][0]) + "-->" + str(sorted_friends_by_number[i][1]))

        net = Network()
        max_friends_common = sorted_friends_by_number[0][1]['same_real_friends_number']
        max_friends_percent = sorted_friends_by_percentage[0][1]['percentage_real_friends_common']
        print(max_friends_common, max_friends_percent)
        max_point = 10
        leveler_percent = max_point / max_friends_percent
        leveler_raw = max_point / max_friends_common

        c1 = '#00ffe5'
        c2 = '#007fff'

        for i in range(len(sorted_friends_by_number)):
            net.add_node(n_id=sorted_friends_by_number[i][1]['id'], label=str(sorted_friends_by_number[i][0]),
                         size=(sorted_friends_by_number[i][1][
                                   'same_real_friends_number'] * leveler_raw + 1),
                         color=colorFader(c2, c1, sorted_friends_by_number[i][1][
                             'same_real_friends_number'] / max_friends_common))

        for i in range(len(sorted_friends_by_number)):
            for edge in all_data[sorted_friends_by_number[i][1]['id']]:
                try:
                    net.add_edge(sorted_friends_by_number[i][1]['id'], edge)
                except Exception:
                    pass
        net.show_buttons(filter_=['physics'])
        net.show("./generatedFiles/graph.html")

        return result

    def all_data_graph(self):
        user = User("Fake")
        users = user.find_all(self.db_client.database)
        net = Network()
        result = {}
        max_friends = 0
        max_point = 15
        c1 = '#00ffe5'
        c2 = '#007fff'
        for user in users:
            friends, opt_result = self.get_real_friends(user["username"], optimized=True)
            result[user["insta_id"]] = friends
            max_friends = max(max_friends, len(friends.keys()))
        users.rewind()
        for user2 in users:
            net.add_node(n_id=user2["insta_id"],
                         label=user2["username"],
                         size=max_point * len(result[user2["insta_id"]].keys()) / max_friends,
                         color=colorFader(c2, c1, len(result[user2["insta_id"]].keys()) / max_friends))
        users.rewind()
        for user3 in users:
            for friends in result[user3["insta_id"]]:
                try:
                    net.add_edge(user3["insta_id"], friends)
                except Exception:
                    pass
        net.show_buttons(filter_=['physics'])
        net.show("./generatedFiles/all_graph.html")


def colorFader(c1, c2, mix=0):  # fade (linear interpolate) from color c1 (at mix=0) to c2 (mix=1)
    c1 = np.array(mpl.colors.to_rgb(c1))
    c2 = np.array(mpl.colors.to_rgb(c2))
    return mpl.colors.to_hex((1 - mix) * c1 + mix * c2)
