import sys
import os, django
from tqdm import tqdm
import collections
import spacy

nlp = spacy.load("en_core_web_sm")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "socioscope.settings")
django.setup()
sys.path.append('./event_detection')
import pandas as pd
from django.contrib.auth.models import User
from event_detection.models import Tweet, Keyword, Knowledge, Trends, Events, Unique_knowledge
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_aware, make_aware
from event_detection.utils import knowledge_graph_extract, text_utils, utils, event_detect

import json

# https://stackoverflow.com/questions/48034725/tweepy-connection-broken-incompleteread-best-way-to-handle-exception-or-can
import sys
import time
import schedule
import time
import datetime
import tweepy
import json
from event_detection.models import Tweet, Keyword, TwitterToken, Knowledge, Trends, TopicsDB, Temporal_knowledge
from queue import Queue
from threading import Thread
from tweepy.models import Status
import dateutil.parser
import time
from django.utils import timezone
from event_detection.utils import knowledge_graph_extract, text_utils, utils, datetime_utils, dbpedia_query
from event_detection.utils import event_detect
from django.utils.timezone import make_aware
from langdetect import detect
from pymongo import MongoClient
from datetimerange import DateTimeRange
import datetime as dt

MONGO_HOST = "mongodb://localhost:27017/socialrainbow"
myclient = MongoClient("mongodb://localhost:27017/")

mydb = myclient["socialrainbow"]
db = myclient["kisti"]
tweet_col = db["한국_"]


# countries_col = mydb["countries"]


# knowledge_col = mydb['knowledge_sm_data']
def import_related_keyword(keyword_obj):
    related_topics = utils.suggest_keyword_from_dbpedia(keyword_obj.id)
    print(related_topics)
    if related_topics != None:
        for topic in related_topics:
            TopicsDB.objects.create(keyword=keyword_obj, related_topic=topic)
    return True


def import_tweets(keyword_obj):
    old_unique_knowledge = Unique_knowledge.objects.filter(keyword=keyword_obj)
    old_unique_knowledge_text = []
    for tmp in old_unique_knowledge:
        old_unique_knowledge_text.append(str(tmp))
    f = open("tweet_text_korea.txt", "a")
    cursor = tweet_col.find({}, no_cursor_timeout=True)
    for line in tqdm(cursor):
        try:
            # print(make_aware(line['created_at']), type(line['created_at']))
            # if make_aware(line['created_at']) >= keyword_obj.search_date:
                tweet_obj = Tweet.objects.create(keyword=keyword_obj,
                                                 tweet_id=line['tweet_id'],
                                                 created_at=make_aware(line['created_at']),
                                                 # original_tweet_id=line['original_tweet_id'],
                                                 # retweet_count=line['retweetCount'],
                                                 # favorite_count=line['favorite_count'],
                                                 original_tweet_id='',
                                                 retweet_count=0,
                                                 favorite_count=0,
                                                 text=line['tweet'],
                                                 country=line['country'],
                                                 )
                text = text_utils.pre_process(line['tweet'])
                f.write(text)

                triple_list = knowledge_graph_extract.extract_entity(text, nlp)

                for triple in triple_list:
                    if len(triple) == 5:
                        try:
                            Knowledge.objects.create(tweet=tweet_obj,
                                                     keyword=keyword_obj,
                                                     k_subject=triple[0],
                                                     k_predicate=triple[1],
                                                     k_object=triple[2],
                                                     subject_type=triple[3],
                                                     object_type=triple[4],
                                                     is_new_knowledge="")
                            tmp_knowledge = triple[0] + ', ' + triple[1] + ', ' + triple[2]
                            # print(tmp_knowledge)
                            # print(old_unique_knowledge_text)
                            if tmp_knowledge not in old_unique_knowledge_text:
                                old_unique_knowledge_text.append(tmp_knowledge)
                                Unique_knowledge.objects.create(keyword=keyword_obj,
                                                                k_subject=triple[0],
                                                                k_predicate=triple[1],
                                                                k_object=triple[2]
                                                                )
                        except:
                            continue
        except:
            continue
    cursor.close()
    f.close()
    # fn = open("tweet_text_korea.txt", "r")
    # st = fn.read()
    # print("done read txt")
    #
    # all_stopwords = nlp.Defaults.stop_words
    # add = ['amp', 'via', 'cc', 'RT', 'dont', 'cant', 'doesnt', '&amp', 'must', 'need', 'get', 'youre', 'gon',
    #        'im', 'na']
    # # text_list = st.replace(".",' ')
    # text_list = st.replace("&amp", '')
    # text_list = text_list.replace("via", '')
    # text_list = text_list.replace("RT", '')
    # text_list = text_list.replace("dont", '')
    # text_list = text_list.replace("cant", '')
    # text_list = text_list.replace("doesnt", '')
    # text_list = text_list.replace("must", '')
    # text_list = text_list.replace("need", '')
    # text_list = text_list.replace("get", '')
    # text_list = text_list.replace("youre", '')
    # text_list = text_list.replace("gon", '')
    # text_list = text_list.strip()
    # text_list = text_list.split(".")
    # ngrams = []
    # for text in tqdm(text_list):
    #     text = text.strip()
    #     ngrams = ngrams + utils.extract_ngrams(text, nlp)
    # print("done ngrams", len(ngrams))
    # # ngrams = text_list.split(" ")
    # # print(len(ngrams))
    # # print(len(all_stopwords))
    # new_ngrams = [ele for ele in ngrams if (ele not in all_stopwords) and (ele not in add)]
    # print(len(new_ngrams))
    # counter = collections.Counter(new_ngrams)
    # print("done ngram import", len(new_ngrams))
    # ngram_new = list(set(new_ngrams))
    # print("done ngram new", len(ngram_new))
    # for ngram in tqdm(ngram_new):
    #     if len(ngram) >= 3 and (ngram.isnumeric() == False):
    #         trends_object = Trends.objects.create(keyword=keyword_obj,
    #                                               trend=ngram,
    #                                               notrend=counter[ngram]
    #                                               # tweet_id=status.id
    #                                               )
    #
    # fn.close()


def get_top_trend(pk):
    # trend_list = Trends.objects.filter(keyword=pk)
    top_trends = []
    pk = int(pk)
    # print("pk: ",pk, type(pk))

    raw_trends = Trends.objects.raw(
        "SELECT 1 as id, trend FROM public.event_detection_trends WHERE keyword_id = '%s' ORDER BY notrend DESC LIMIT 100 ",

        [pk])
    for trend in raw_trends:
        top_trends.append(str(trend))
    return top_trends


def get_top_trend_countries(pk, countries):
    trends_list = []
    for country in tqdm(countries):
        top_trends = Trends.objects.filter(keyword_id=pk, country=country).order_by('-notrend')[:30]
        for trend in top_trends:
            if trend.trend not in trends_list:
                trends_list.append(trend.trend)
    return trends_list


def tweets_countries(keyword_obj):
    tweets_list = utils.get_tweet_in_time_range_countries(keyword_obj.id, "", "", countries, '')
    return tweets_list


def event_detection(keyword_obj):
    keyword_id = keyword_obj.id
    top_trends = get_top_trend_countries(keyword_id, countries)
    # bursts = []
    # x_data_date_group = keyword_obj.x_data_date
    # y_data_group = keyword_obj.y_data
    # # print(trends_list)
    # # print(x_data_date_group)
    # # print(y_data_group)
    # tweet_list = Tweet.objects.filter(keyword_id=keyword_id)
    # x_data_date, y_data = event_detect.get_tweet_distribution(tweet_list, "hour", "")
    # tmp_time = []
    # for tweet in tweet_list:
    #     tmp_time.append(tweet.created_at)
    # start_date = datetime_utils.correct_time(min(tmp_time).strftime("%Y-%m-%d %H"))
    # end_date = datetime_utils.correct_time(max(tmp_time).strftime("%Y-%m-%d %H"))
    # time_range = DateTimeRange(start_date, end_date)
    # time = []
    # for value in time_range.range(dt.timedelta(hours=1)):
    #     time.append(value.strftime("%Y-%m-%d %H:%M"))
    #
    # y_data_final = [0] * len(time)
    # for x in time:
    #     for x_date in x_data_date:
    #         if x == x_date:
    #             y_data_final[time.index(x)] = y_data[x_data_date.index(x_date)]
    # y_data_final_new = [element * 1000 for element in y_data_final]

    for trend in tqdm(top_trends):
        # country_index = top_trends_list.index(trends_list)
        trend_obj = Trends.objects.filter(keyword_id=keyword_id, trend=trend)[0]
        for i in (range(len(countries))):
            # burst_list, variables = event_detect.detect_event(trend_obj.y_data_event[i],
            #                                                   keyword_obj.y_data[i])
            #     try:
            #     print(trend, countries)
            try:
                y_data_event = [element * 1000 for element in trend_obj.y_data_event[i]]
                y_data_final_new = [element * 1000 for element in keyword_obj.y_data[i]]
                # print(len(y_data_event), len(y_data_final_new))
                # break
                burst_list, variables = event_detect.detect_event(y_data_event,
                                                                  y_data_final_new)

            except Exception as e:
                print(trend_obj, countries[i])
                print('exception:', e)
            # # try:
            if burst_list != []:
                # print(burst_list)
                # for bursts in burst_list:
                # print(bursts)
                bursts = burst_list[0]
                for index, burst in bursts.iterrows():
                    if burst['weight'] != 'NaN' and burst['weight'] != 'inf':
                        # if burst['weight'] >= 10:
                        start = burst['begin']
                        end = burst['end']
                        start_time = keyword_obj.x_data_date[i][start]  # .strftime("%Y-%m-%d %H:%M")
                        end_time = keyword_obj.x_data_date[i][end]  # .strftime("%Y-%m-%d %H:%M")
                        raw_events = Events.objects.filter(keyword=keyword_id, trend=trend,
                                                           country=countries[i], begin_time=start_time,
                                                           end_time=end_time)
                        # print(len(raw_events))
                        if len(raw_events) != 0:
                            # if len(x_data_hour) < 12:
                            print("start time ", start_time)
                            print("end time ", end_time)
                            Events.objects.create(keyword=keyword_obj,
                                                  begin_time=start_time,
                                                  end_time=end_time,
                                                  trend=trend,
                                                  country=countries[i])


def insert_db_check(keyword_obj):
    temporal_knowledge = Temporal_knowledge.objects.filter(keyword=keyword_obj)
    for knowledge in tqdm(temporal_knowledge):
        # print(knowledge.is_new_knowledge)
        if knowledge.is_new_knowledge == None:
            # print("check: ",knowledge.is_new_knowledge)
            try:
                db_knowledge_subj = dbpedia_query.check_link_DBpedia(knowledge.k_subject)
                db_knowledge_obj = dbpedia_query.check_link_DBpedia(knowledge.k_object)
                if db_knowledge_subj:
                    check_subj = 'true'
                else:
                    check_subj = 'false'
                if db_knowledge_obj:
                    check_obj = 'true'
                else:
                    check_obj = 'false'
                check = check_subj + '-' + check_obj
                # print(check)
                Temporal_knowledge.objects.filter(keyword=keyword_obj, k_subject=knowledge.k_subject,
                                                  k_predicate=knowledge.k_predicate,
                                                  k_object=knowledge.k_object).update(
                    is_new_knowledge=check)
            except:
                continue
        # break


if __name__ == "__main__":
    keyword_obj = Keyword.objects.filter(id='466')[0]
    # keyword_obj = Keyword.objects.filter(id='431')[0]
    # 423 is newspaper data
    print(keyword_obj.search_date)
    # countries = keyword_obj.countries
    # import_related_keyword(keyword_obj)
    import_tweets(keyword_obj)
    # # # # insert_db_check(keyword_obj)
    # event_detection(keyword_obj)
    # knowledge_graph_extract.get_temporal_knowledge(keyword_obj)
