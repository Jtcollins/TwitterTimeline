import twitter
from twitter.stream import TwitterStream, Timeout, HeartbeatTimeout, Hangup
from twitter.oauth import OAuth
from twitter.oauth2 import OAuth2, read_bearer_token_file
from twitter.util import printNicely
from string import ascii_letters
import os
import re
import string
import sys

# XXX: Go to http://dev.twitter.com/apps/new to create an app and get values
# for these credentials, which you'll need to provide in place of these
# empty string values that are defined as placeholders.
# See https://dev.twitter.com/docs/auth/oauth for more information
# on Twitter's OAuth implementation.

API_KEY = '***'
API_SECRET = '***'
OAUTH_TOKEN = '***'
OAUTH_TOKEN_SECRET = '***'

DEFAULT_HASH = "e"

auth = twitter.oauth.OAuth(OAUTH_TOKEN, OAUTH_TOKEN_SECRET,
                           API_KEY, API_SECRET)

query = DEFAULT_HASH
count = 10000

twitter_api = twitter.Twitter(auth=auth)


def make_tweet(text, time, lat, lon):
    """Return a tweet, represented as a Python dictionary.

    text  -- A string; the text of the tweet, all in lowercase
    time  -- A datetime object; the time that the tweet was posted
    lat   -- A number; the latitude of the tweet's location
    lon   -- A number; the longitude of the tweet's location

    >>> t = make_tweet("just ate lunch", datetime(2012, 9, 24, 13), 38, 74)
    >>> tweet_words(t)
    ['just', 'ate', 'lunch']
    >>> tweet_time(t)
    datetime.datetime(2012, 9, 24, 13, 0)
    >>> p = tweet_location(t)
    >>> latitude(p)
    38
    """
    return {'text': text, 'time': time, 'latitude': lat, 'longitude': lon}

def tweet_words(tweet):
    """Return a list of the words in the text of a tweet."""
    t = tweet['text']
    return t.split()

def tweet_time(tweet):
    """Return the datetime that represents when the tweet was posted."""
    return tweet['time']

def tweet_location(tweet):
    """Return a position (see geo.py) that represents the tweet's location."""
    return make_position(tweet['latitude'], tweet['longitude'])

def tweet_string(tweet):
    """Return a string representing the tweet."""
    location = tweet_location(tweet)
    return '"{0}" @ {1}'.format(tweet['text'], (latitude(location), longitude(location)))

def extract_words(text):
    """Return the words in a tweet, not including punctuation.

    >>> extract_words('anything else.....not my job')
    ['anything', 'else', 'not', 'my', 'job']
    >>> extract_words('i love my job. #winning')
    ['i', 'love', 'my', 'job', 'winning']
    >>> extract_words('make justin # 1 by tweeting #vma #justinbieber :)')
    ['make', 'justin', 'by', 'tweeting', 'vma', 'justinbieber']
    >>> extract_words("paperclips! they're so awesome, cool, & useful!")
    ['paperclips', 'they', 're', 'so', 'awesome', 'cool', 'useful']
    >>> extract_words('@(cat$.on^#$my&@keyboard***@#*')
    ['cat', 'on', 'my', 'keyboard']
    """
    

    i = 0
    if type(text) == str:
        while i<len(text):
            if text[i] not in ascii_letters:
                text = text.replace(text[i], " ")
            i+=1
        return text.split()
    else:
        def remove_from_list(string):
            if string[i] not in ascii_letters:
                string = string.replace(text[i], "")
            return string
        return [remove_from_list(word) for word in text]

# Look for data directory
PY_PATH = sys.argv[0]
if PY_PATH.endswith('doctest.py') and len(sys.argv) > 1:
    PY_PATH = sys.argv[1]
DATA_PATH = os.path.join(os.path.dirname(PY_PATH), 'data') + os.sep
if not os.path.exists(DATA_PATH):
    DATA_PATH = 'data' + os.sep

def load_sentiments(file_name=DATA_PATH + "sentiments.csv"):
    """Read the sentiment file and return a dictionary containing the sentiment
    score of each word, a value from -1 to +1.
    """
    sentiments = {}
    for line in open(file_name):
        word, score = line.split(',')
        sentiments[word] = float(score.strip())
    return sentiments

word_sentiments = load_sentiments()

def make_sentiment(value):
    """Return a sentiment, which represents a value that may not exist.

    >>> positive = make_sentiment(0.2)
    >>> neutral = make_sentiment(0)
    >>> unknown = make_sentiment(None)
    >>> has_sentiment(positive)
    True
    >>> has_sentiment(neutral)
    True
    >>> has_sentiment(unknown)
    False
    >>> sentiment_value(positive)
    0.2
    >>> sentiment_value(neutral)
    0
    """
    assert value is None or (value >= -1 and value <= 1), 'Illegal value'
    if value is None:
        return (False, value)
    else:
        return (True, value)

def has_sentiment(s):
    """Return whether sentiment s has a value."""
    return s[0]

def sentiment_value(s):
    """Return the value of a sentiment s."""
    assert has_sentiment(s), 'No sentiment value'
    return s[1]

def get_word_sentiment(word):
    """Return a sentiment representing the degree of positive or negative
    feeling in the given word.

    >>> sentiment_value(get_word_sentiment('good'))
    0.875
    >>> sentiment_value(get_word_sentiment('bad'))
    -0.625
    >>> sentiment_value(get_word_sentiment('winning'))
    0.5
    >>> has_sentiment(get_word_sentiment('Berkeley'))
    False
    """
    # Learn more: http://docs.python.org/3/library/stdtypes.html#dict.get
    return make_sentiment(word_sentiments.get(word))

def analyze_tweet_sentiment(tweet):
    """ Return a sentiment representing the degree of positive or negative
    sentiment in the given tweet, averaging over all the words in the tweet
    that have a sentiment value.

    If no words in the tweet have a sentiment value, return
    make_sentiment(None).

    >>> positive = make_tweet('i love my job. #winning', None, 0, 0)
    >>> round(sentiment_value(analyze_tweet_sentiment(positive)), 5)
    0.29167
    >>> negative = make_tweet("saying, 'i hate my job'", None, 0, 0)
    >>> sentiment_value(analyze_tweet_sentiment(negative))
    -0.25
    >>> no_sentiment = make_tweet("berkeley golden bears!", None, 0, 0)
    >>> has_sentiment(analyze_tweet_sentiment(no_sentiment))
    False
    """
    average = make_sentiment(None)
    i = 0
    analyzed = 0
    count = 0
    tweet_text = extract_words(tweet_words(tweet))
    while i<len(tweet_text):
        if has_sentiment(get_word_sentiment(tweet_text[i])):
            analyzed = analyzed + sentiment_value(get_word_sentiment(tweet_text[i]))
            count = count + 1
        i = i + 1
    if analyzed == 0:
        return make_sentiment(None)
    return make_sentiment(analyzed/count)

def main():

    query_args = dict()
    query_args['track'] = query

    stream = TwitterStream(auth=auth)
    tweet_iter = stream.statuses.filter(**query_args)
    #tweet_iter = stream.statuses.sample()
    tweets = []
    # Iterate over the sample stream.
    for tweet in tweet_iter:
        # You must test that your tweet has text. It might be a delete
        # or data message.
        if tweet is None:
            print("-- None --")
        elif tweet is Timeout:
            print("-- Timeout --")
        elif tweet is HeartbeatTimeout:
            print("-- Heartbeat Timeout --")
        elif tweet is Hangup:
            print("-- Hangup --")
        elif tweet.get('text'):
        	senti = analyze_tweet_sentiment(tweet)
        	if (tweet.get('coordinates') != None):
        		curr = [tweet.get('coordinates'), senti]
        		tweets.append(curr)
        		#print(tweets)
        else:
            print("-- Some data: " + str(tweet))

if __name__ == '__main__':
    main()


