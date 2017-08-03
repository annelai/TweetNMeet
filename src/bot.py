import tweepy
from tweepy import streaming
from tweepy import OAuthHandler
from tweepy import Stream

from config import *

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)

class StreamListener(streaming.StreamListener):

	def on_status(self, status):
		user_screen_name = status.user.screen_name
		tweet_id = status.id_str
		created_at = status.created_at
		loc = status.user.location
		coords = status.coordinates

		## TODO: add optional paramters
		# text = status.text

		TweetNMentBot(user_screen_name, tweet_id, created_at, loc, coords)
		TweetNMentBot.run()

    def on_error(self, status_code):
        if status_code == 420:
            return False

class TweetNMentBot(Object):
	def __init__(self, user_screen_name, tweet_id, created_at, loc, coords):
		self.user_screen_name = user_screen_name
		self.tweet_id = tweet_id
		self.created_at = created_at
		self.loc = loc
		self.coords =coords

	def run(self):
		get_public_tweets()
		fetch_meetups()
		reply_tweet()
		
	def get_public_tweets(self):
		public_tweets = api.user_timeline(screen_name=self.user_screen_name, max_id=self.tweet_id)
		tweets = []
		for public_tweet in public_tweets:
			text = public_tweet['text']
			hashtags = []
			list_of_indices = []
			for hashtag in public_tweet['entities']['hashtags']:
				hashtags.append(hashtag['text'])
				list_of_indices.append(hashtag['indices'])
			for media in public_tweet['media']:
				list_of_indices.append(media['indices'])
	
			plain_text = utils.get_plain_text(text, list_of_indices)
			tweets.append({'text': text, 'plain_text':plain_text, 'hashtags':hashtags})
	
	def fetch_meetups(self):
		self.list_of_meetups = []

	def reply_tweet(self):
		meetupText = ""
		for meetup in self.list_of_meetups:
			meetupText += """
		> {title}
		%{url}""".format(title=meetup['title'], url=meetup['url'])
		replyText = """
		Hey! @{user_screen_name},
		you might be interested in these meetups:
		{meetupText}
		""".format(user_screen_name=self.user_screen_name, meetupText=meetupText)
	
		api.update_status(replyText, self.tweet_id)

if __name__ == '__main__':
	stream_listener = StreamListener()
	stream = tweepy.Stream(auth=api.auth, listener=stream_listener)
	stream.filter(track=["@MeetupBot"], async=True)