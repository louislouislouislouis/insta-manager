# sys import
import json
import sys
import os
import re
import time
import random

# selenium libraries
from selenium import webdriver
from selenium.common.exceptions import TimeoutException

# personal import
from instaManager.exception import *
from instaManager.interaction.interaction import click
from instaManager.interaction.interaction import get
from instaManager.interaction.interaction import send_keys
from instaManager.logger.log import Log

# const
XPATH_FILENAME = os.path.join(os.path.dirname(__file__), 'config/xpath.json')
URL_FILENAME = os.path.join(os.path.dirname(__file__), 'config/url.json')
COMMENTS_FILENAME = os.path.join(os.path.dirname(__file__), 'data/comments.json')
HASHTAGS_FILENAME = os.path.join(os.path.dirname(__file__), 'data/hashtags.json')


class InstaManager:
    def __init__(self, username, password, private=True):

        self.username = username
        self.password = password
        self.is_connected = False
        self.logger = Log("INSTAMANAGER")

        # Json option
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

        self.driver = webdriver.Chrome("./chromedriver", options=chrome_options)
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
            self.logger.print("Trouble connecting in insta", type="ERROR", color="red", method="CONNECT")
            self.logger.print(bad_except, "ERROR", color="red", method="CONNECT")

    def find_and_comment_post_by_tag(self, tags, percentage_like=0.5, percentage_comment=0.5, sleep_time=20):
        if not self.is_connected:
            raise NotConnectedError.NotConnectedError()
        else:
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
                    if media["media"]["caption"]["text"]:
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
                if random.random() < percentage_comment * post_id["level"]:
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
                    self.logger.print("Just comment a level " + str(post_id["level"]) + " post", color="blue",
                                      method="FIND AND INTERACT BY TAGS")

                # like conditional
                if random.random() < percentage_like * post_id["level"]:
                    click(self.driver, self.xpath.get("post_page").get("like_button"), )
                    self.logger.print("Just lik a level " + str(post_id["level"]) + " post", color="blue",
                                      method="FIND AND INTERACT BY TAGS")

                # sleep before next iteration
                self.logger.print("Just finish interacting a post of level " + str(post_id["level"]), color="blue",
                                  method="FIND AND INTERACT BY TAGS")
                time.sleep(sleep_time)
