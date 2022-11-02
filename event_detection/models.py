import re
from django.db import models
from django.utils import timezone
from datetime import date
from django.conf import settings
from django.contrib.auth.models import User
import json
from django.contrib.postgres.fields import ArrayField
import jsonfield
# Create your models here.

class TwitterToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=User.objects.get(pk=1).id,
                             related_name='tokens')
    consumer_key = models.CharField(max_length=100)
    consumer_secret = models.CharField(max_length=100)
    access_token = models.CharField(max_length=100)
    access_token_secret = models.CharField(max_length=100)
    used_count = models.IntegerField(default=0)
    token_check = models.BooleanField()
    def __str__(self):
        return self.consumer_key

class Countries(models.Model):
    country_name = models.CharField(max_length=255)
    country_code = models.CharField(max_length=255)
    place_id = models.CharField(max_length=255)
    def __str__(self):
        return self.country_name

class Keyword(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=User.objects.get(pk=1).id,
                             related_name='keywords')
    # id = models.AutoField(primary_key=True)
    keyword = models.CharField(max_length=200)
    search_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    is_streaming = models.BooleanField(default=True)
    error_code = models.IntegerField(default=0)
    is_forced_stop = models.BooleanField(default=False)
    x_data_date = jsonfield.JSONField()
    y_data = jsonfield.JSONField()
    countries = jsonfield.JSONField()
    resource = models.IntegerField()
    def __str__(self):
        return self.keyword


class Tweet(models.Model):
    keyword = models.ForeignKey('event_detection.Keyword', on_delete=models.CASCADE, related_name='tweets')
    tweet_id = models.BigIntegerField()
    created_at = models.DateTimeField()
    # user_id = models.BigIntegerField()
    # retweeted_id = models.BigIntegerField()
    # quoted_id = models.BigIntegerField()
    text = models.TextField()
    # quoted_text = models.TextField()

    #country
    original_tweet_id = models.TextField()
    retweet_count = models.IntegerField()
    favorite_count = models.IntegerField()
    country = models.TextField()

    #sentiment
    label = models.TextField()
    score = models.DecimalField(blank=True, null=True, max_digits=20,  decimal_places=10)

    def __str__(self):
        return self.text

class TopicsDB(models.Model):
    id = models.AutoField(primary_key=True)
    keyword = models.ForeignKey('event_detection.Keyword', on_delete=models.CASCADE, related_name='topicsDB')
    related_topic = models.TextField()

    def __str__(self):
        return self.related_topic

class Trends(models.Model):
    id = models.AutoField(primary_key=True)
    keyword = models.ForeignKey('event_detection.Keyword', on_delete=models.CASCADE, related_name='trends')
    trend = models.TextField()
    notrend = models.IntegerField()
    x_data_date_event = jsonfield.JSONField()
    y_data_event = jsonfield.JSONField()
    y_proportion = jsonfield.JSONField()
    y_pos_sentiment = jsonfield.JSONField()
    y_neg_sentiment = jsonfield.JSONField()
    y_neu_sentiment = jsonfield.JSONField()
    country = models.TextField()
    def __str__(self):
        return self.trend

class Events(models.Model):
    id = models.AutoField(primary_key=True)
    keyword = models.ForeignKey('event_detection.Keyword', on_delete=models.CASCADE, related_name='events')
    trend = models.TextField()
    begin_time = models.TextField()
    end_time = models.TextField()
    country = models.TextField()

    def __str__(self):
        return ", ".join([self.begin_time,self.end_time])


class Temporal_knowledge(models.Model):
    id = models.AutoField(primary_key=True)
    keyword = models.ForeignKey('event_detection.Keyword', on_delete=models.CASCADE, related_name='temporal_knowledge')
    tweet = models.ForeignKey('event_detection.Tweet', on_delete=models.CASCADE, related_name='temporal_knowledge')
    k_subject = models.TextField()
    k_predicate = models.TextField()
    k_object = models.TextField()
    temporal_start = models.TextField()
    temporal_end = models.TextField()
    mentions = models.IntegerField()
    occurrence = ArrayField(ArrayField(models.IntegerField()))
    diffuse_degree = ArrayField(ArrayField(models.IntegerField()))
    timeline = jsonfield.JSONField()
    diffuse_sensitivity = ArrayField(ArrayField(models.IntegerField()))
    group_tweets_id = ArrayField(ArrayField(models.IntegerField()))
    is_new_knowledge = models.CharField(max_length=100, default='')
    def __str__(self):
        return ", ".join([self.k_subject, self.k_predicate, self.k_object])
class Unique_knowledge(models.Model):
    id = models.AutoField(primary_key=True)
    keyword = models.ForeignKey('event_detection.Keyword', on_delete=models.CASCADE, related_name='unique_knowledge')
    # tweet = models.ForeignKey('event_detection.Tweet', on_delete=models.CASCADE, related_name='knowledge')
    k_subject = models.TextField()
    k_predicate = models.TextField()
    k_object = models.TextField()
    # country = models.TextField()
    def __str__(self):
        return ", ".join([self.k_subject, self.k_predicate, self.k_object])


class Knowledge(models.Model):
    tweet = models.ForeignKey('event_detection.Tweet', on_delete=models.CASCADE, related_name='knowledge')
    keyword = models.ForeignKey('event_detection.Keyword', on_delete=models.CASCADE, related_name='knowledge')
    k_subject = models.TextField()
    k_predicate = models.TextField()
    k_object = models.TextField()
    subject_type = models.CharField(max_length=100, default='')
    object_type = models.CharField(max_length=100, default='')
    is_new_knowledge = models.CharField(max_length=100, default='')

    def __str__(self):
        # return ", ".join([self.k_subject, self.k_predicate, self.k_object, self.subject_type, self.object_type])
        return ", ".join([self.k_subject, self.k_predicate, self.k_object])
