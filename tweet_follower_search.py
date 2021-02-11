import tweepy
import time
import pandas as pd

def tweepy_authentication(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET):
    # Authenticate to Twitter
    auth = tweepy.OAuthHandler(consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

    # build a api object, set the flag wait no rate limit to True
    api = tweepy.API(auth, retry_count=5, retry_delay=1, wait_on_rate_limit=False, wait_on_rate_limit_notify=False)
    try:
        api.verify_credentials()
        print("Authentication OK")
    except:
        print("Error during authentication")

    return api

#This function make multiple apis for continuing when rate limit has been hit for the API
def multi_authentication(token_list_path):
    f = open(token_list_path)
    api_list = []
    for line in f:
        CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET = line.strip().split(' ')
        api_list.append(tweepy_authentication(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET))
    
    return api_list

#This function gets the list of follower of a certain user
def get_followers(scn, api_list, currentAPI):

    currentAPI = 0
    next_cursor = -1
    currentCursor = tweepy.Cursor(api_list[currentAPI].followers_ids, screen_name= scn, cursor= next_cursor)
    c = currentCursor.pages()
    next_cursor = c.next_cursor
    followers = []
    while True:
        try:
            user= next(c)
            followers.extend(user)

        except tweepy.TweepError:
            print("Rate limit hit")
            if (currentAPI < len(api_list) - 1):
                print("Switching to next set in constellation")
                currentAPI =  currentAPI + 1
                #print('Problem 1')
                next_cursor = c.next_cursor
                currentCursor = tweepy.Cursor(api_list[currentAPI].followers_ids, screen_name= scn, cursor = next_cursor)
                #print('Problem 2')
                c = currentCursor.pages()
                continue
            else:
                print("All sats maxed out, waiting and will try again")
                currentAPI = 0
                #print('Problem 3')
                next_cursor = c.next_cursor
                currentCursor = tweepy.Cursor(api_list[currentAPI].followers_ids, screen_name= scn, cursor = next_cursor)
                #print('Problem 4')
                c = currentCursor.pages()
                print('Time to sleep')
                time.sleep(60 * 15)
                continue


        except StopIteration:
            break
    
    return currentAPI, followers



#This functio gets the information of the certain user.
def get_user_info(user_id, api_list, currentAPI):

    api = api_list[currentAPI]

    try:
        user = api.get_user(user_id = user_id)

    except tweepy.error.TweepError:
        print("Rate limit hit")
        if (currentAPI < len(api_list) - 1):
            print("Switching to next set in constellation")
            temp = currentAPI
            currentAPI = currentAPI + 1
            api = api_list[currentAPI]
            try:
                user = api.get_user(user_id = user_id)
            except tweepy.error.TweepError:
                print('The account does not exist or user is not authorized')
                currentAPI = temp
                user = 1
                return currentAPI, user
        else:
            print("Returning to first API")
            currentAPI = 0
            api = api_list[currentAPI]
            try:
                user = api.get_user(user_id = user_id)
            except tweepy.error.TweepError:
                print("All sets maxed out, waiting and will try again")
                time.sleep(60 * 15)
                try:
                    user = api.get_user(user_id = user_id)
                except tweepy.error.TweepError:
                    print('The account does not exist or user is not authorized')
                    user = 1
                    return currentAPI, user

    return currentAPI, user

#Get All Information to DataFrame
def get_user_info_to_dataframe(screen_name, api_list, currentAPI = 0):
    user_list = []
    currentAPI, follower_list= get_followers(screen_name, api_list, currentAPI)
    print(len(follower_list))
    for users in follower_list:
        currentAPI, user = get_user_info(users, api_list, currentAPI)

        if user == 1:
            continue
        else:
            all_users = {'id': user.id, 'Name': user.name,
                          'Statuses Count': user.statuses_count,
                          'Friends Count': user.friends_count,
                          'Screen Name': user.screen_name,
                          'Followers Count': user.followers_count,
                          'Location': user.location,
                          'Language': user.lang,
                          'Created at': user.created_at,
                          'Time zone': user.time_zone,
                          'Geo enable': user.geo_enabled,
                          'Description': user.description,
                          'URL': user.url}
            user_list.append(all_users)
            print(f'Got {user.name} info and appended')
    
    df = pd.DataFrame(user_list)
    df.to_csv(f'{screen_name}_followers_info.csv', index=False, encoding='utf-8')

    return df


if __name__ == '__main__':
    screen_name = 'blueminddivers'
    token_list_path = '/Users/alidali/Downloads/token_list.txt'
    api_list = multi_authentication(token_list_path)
    df = get_user_info_to_dataframe(screen_name, api_list, currentAPI = 0)
