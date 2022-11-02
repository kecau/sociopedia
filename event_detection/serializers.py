from rest_framework import serializers
from event_detection.models import Keyword, Tweet

class KeywordSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Keyword
        fields = ['id', 'keyword', 'search_date', 'end_date', 'is_streaming', 'is_forced_stop']

class TweetSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Tweet
        fields = ['id', 'tweet_id', 'created_at', 'user_id', 'retweeted_id', 'quoted_id', 'text', 'quoted_text']