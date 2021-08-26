from instaManager.instaManager import InstaManager

# login credentials
insta_username = 'magnify_music_app'
insta_password = 'lojR6W25'

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    my_insta_manager = InstaManager(insta_username, insta_password)
    my_insta_manager.connect()
    my_insta_manager.find_and_comment_post_by_tag("indiemusic", percentage_like=0.3, percentage_comment=0.2)
