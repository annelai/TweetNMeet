import re
import pickle
import tweepy
import random
from tweepy import streaming
from tweepy import OAuthHandler
from tweepy import Stream
import urllib.request
from bs4 import BeautifulSoup
from config import *
from utils import *


NUM_RT_EVENTS = 6

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)
topic2keyword = pickle.load(open("model/map","rb"))
ldamodel = pickle.load(open("model/ldamodel.pickle","rb"))

class StreamListener(streaming.StreamListener):
	def on_status(self, status):
		user_screen_name = status.user.screen_name
		tweet_id = status.id_str
		created_at = status.created_at
		loc = status.user.location
		try:
			coords = status.coordinates['coordinates']
		except:
			coords = status.coordinates
		print (loc, coords)
		## TODO: add optional paramters
		# text = status.text
		bot = TweetNMentBot(user_screen_name, tweet_id, created_at, loc, coords)
		bot.run()
	def on_error(self, status_code):
		if status_code == 420:
			return False

class TweetNMentBot:
	def __init__(self, user_screen_name, tweet_id, created_at, loc, coords):
		self.user_screen_name = user_screen_name
		self.tweet_id = tweet_id
		self.created_at = created_at
		self.loc = loc
		self.coords = coords
		
		replyText = "Beep Boop. Got your request, @%s. \nI'm analyzing your tweets to find interesting meetups." % (self.user_screen_name)
		api.update_status(replyText, self.tweet_id)

	def run(self):
		self.get_public_tweets()
		self.fetch_meetups()
		self.reply_tweet()
		
	def get_public_tweets(self):
		public_tweets = api.user_timeline(screen_name=self.user_screen_name, max_id=self.tweet_id)
		self.tweets = []
		for public_tweet in public_tweets:
			text = public_tweet.text
			hashtags = []
			list_of_indices = []
			for hashtag in public_tweet.entities['hashtags']:
				hashtags.append(hashtag['text'])
				list_of_indices.append(hashtag['indices'])
			for url in public_tweet.entities['urls']:
				list_of_indices.append(url['indices'])
	
			plain_text = get_plain_text(text, list_of_indices)
			self.tweets.append({'text': text, 'plain_text':plain_text, 'hashtags':hashtags})


	def get_topics(self):
		doc_term_matrix = flatten(getDocBoW([tweet['text'] for tweet in self.tweets]))
		lda = ldamodel[doc_term_matrix]
		lda.sort(key=lambda x: x[1], reverse=True)
		return [topic_score_pair[0] for topic_score_pair in lda]

	def get_keywords(self):
		topics = self.get_topics()
		keywords = [topic2keyword[topic] for topic in topics]
		return keywords


	def fetch_meetups(self):
		keywords = self.get_keywords()
		print (keywords)
		try:
			zipcode = coords2zipcode(tuple(self.coords))
		except:
			zipcode = coords2zipcode(None)

		self.list_of_meetups = []
		if len(self.tweets) == 0:
			url = "https://www.meetup.com/find/events/radius=50&userFreeform=%s" % (zipcode)
			html = urllib.request.urlopen(url).read()
			soup = BeautifulSoup(html, 'html.parser')
			events = soup.find_all("a",{"class":re.compile("resetLink big event.*")})
			sample_events = random.sample(events, 5)
			for event in sample_events:
				ev_name = event.find(itemprop="name").text
				ev_href = event['href']
				self.list_of_meetups.append(("meetup",ev_name,ev_href))
		else:
			for keyword in keywords:
				url = "https://www.meetup.com/find/events/?keywords=%s&radius=50&userFreeform=%s" % (keyword, zipcode)
				html = urllib.request.urlopen(url).read()
				soup = BeautifulSoup(html, 'html.parser')
				events = soup.find_all("a",{"class":re.compile("resetLink big event.*")})
				sample_events = random.sample(events, 2)
				for event in sample_events:
					ev_name = event.find(itemprop="name").text
					ev_href = event['href']
					self.list_of_meetups.append((keyword,ev_name,ev_href))
				if len(self.list_of_meetups) > NUM_RT_EVENTS:
					break

	def reply_tweet(self):
		replyText = "@%s Hey-o, found you some meetups in %s. Here are your top results:" % (self.user_screen_name ,self.loc)
		api.update_status(replyText, self.tweet_id)

		for meetup in self.list_of_meetups[:NUM_RT_EVENTS]:
			replyText = """@{user_screen_name}
		> {ev_name} #{topic}
		{ev_href}
		""".format(user_screen_name=self.user_screen_name, topic=meetup[0], ev_name=meetup[1], ev_href=meetup[2])
			api.update_status(replyText, self.tweet_id)

if __name__ == '__main__':
	stream_listener = StreamListener()
	stream = tweepy.Stream(auth=api.auth, listener=stream_listener)
	stream.filter(track=["@MeetupBot"], async=True)