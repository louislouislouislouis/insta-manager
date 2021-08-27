import os
import json
import sys
from instaManager.instaManager import InstaManager

# const
PATH_TO_DRIVER = "./chromedriver"
CREDENTIALS_FILENAME = os.path.join(os.path.dirname(__file__), 'credentials2.json')

# get cred info
try:
    f = open(CREDENTIALS_FILENAME)
    my_cred = json.load(f)
    insta_password = my_cred["insta_pw"]
    insta_username = my_cred["insta_login"]
except Exception as bad_except:
    print(bad_except)
    sys.exit()

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    my_insta_manager = InstaManager(PATH_TO_DRIVER, insta_username, insta_password, headless=False)
    my_insta_manager.connect()
    print('ee')
    my_insta_manager.get_friendship_status()
    # list1, list2, list3 = my_insta_manager.get_follow_data("louis.lmbrd")

    # my_insta_manager.find_and_comment_post_by_tag("indiemusic", percentage_like=0.2, percentage_comment=0.2)
