# https://stackoverflow.com/questions/48034725/tweepy-connection-broken-incompleteread-best-way-to-handle-exception-or-can
import sys
import time
import schedule
import time
import datetime
import tweepy
import json
from event_detection.models import Tweet, Keyword, TwitterToken, Knowledge, Trends, TopicsDB, Unique_knowledge
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


class StreamListener(tweepy.StreamListener):
    def __init__(self, keyword_obj_list, used_token, nlp, q=Queue()):
        super(StreamListener, self).__init__()
        num_worker_threads = 4
        self.q = q
        self.keyword_obj_list = keyword_obj_list
        self.nlp = nlp
        print("---Init stream listener")
        for i in range(num_worker_threads):
            t = Thread(target=self.save_tweets)
            t.daemon = True
            t.start()
        self.used_token = used_token
        self.end_date = self.keyword_obj_list[0].end_date
        self.is_continue = True

    def on_data(self, raw_data):
        try:
            self.q.put(raw_data)
        except Exception as e:
            print("On data error ", e)

        # # Check streaming every 15 seconds
        # if int(time.time()) % 15 == 0:
        #     self.is_continue = self.stop_streaming()
        #
        # return self.is_continue

    def save_tweets(self):
        keyword_ev = self.keyword_obj_list[0]
        nlp = self.nlp
        # print("check self: ",keyword.id, type(keyword.id))
        try:
            # schedule.every().hour.do(event_detect.auto_detect,keyword_ev)
            schedule.every().day.at("12:00").do(event_detect.auto_detect, keyword_ev)
            schedule.every().day.at("12:00").do(knowledge_graph_extract.get_temporal_knowledge, keyword_ev)

        except:
            print("detect error")
        while True:
            raw_data = self.q.get()
            schedule.run_pending()
            time.sleep(1)
            try:
                data = json.loads(raw_data)
                if 'in_reply_to_status_id' in data:
                    status = Status.parse(self.api, data)

                    is_retweet = False
                    retweeted_id = 0
                    if hasattr(status, 'retweeted_status'):
                        is_retweet = True
                        retweeted_id = status.retweeted_status.id

                        if hasattr(status.retweeted_status, 'extended_tweet'):
                            text = status.retweeted_status.extended_tweet['full_text']
                        else:
                            text = status.retweeted_status.text

                    else:
                        if hasattr(status, 'extended_tweet'):
                            text = status.extended_tweet['full_text']
                        else:
                            text = status.text

                    is_quote = hasattr(status, "quoted_status")
                    quoted_text = ""
                    quoted_id = 0
                    if is_quote:
                        quoted_id = status.quoted_status.id

                        if hasattr(status.quoted_status, "extended_tweet"):
                            quoted_text = status.quoted_status.extended_tweet["full_text"]
                        else:
                            quoted_text = status.quoted_status.text
                    # print(self.keyword_obj_list)
                    for keyword_obj in self.keyword_obj_list:
                        keyword = keyword_obj.keyword
                        # print("keyword: ",keyword)
                        if keyword.lower() in text.lower() or keyword.lower() in quoted_text.lower():
                            if status.lang == 'en':
                                tweet_obj = Tweet.objects.create(keyword=keyword_obj,
                                                                 tweet_id=status.id,
                                                                 created_at=make_aware(status.created_at),
                                                                 user_id=status.user.id,
                                                                 retweeted_id=retweeted_id,
                                                                 quoted_id=quoted_id,
                                                                 text=text,
                                                                 quoted_text=quoted_text)

                                lang = detect(keyword)
                                text = text_utils.pre_process(text)

                                # extract ngram
                                trends_object_list = []
                                trends_object_list_text = []
                                trends_old = Trends.objects.filter(keyword=keyword_obj)
                                for tmp in trends_old:
                                    trends_object_list.append(tmp)
                                    trends_object_list_text.append(str(tmp))
                                ngrams = utils.extract_ngrams(text, nlp)
                                for ngram in ngrams:
                                    if len(ngram) >= 3:
                                        if ngram not in trends_object_list_text:
                                            trends_object = Trends.objects.create(keyword=keyword_obj,
                                                                                  trend=ngram,
                                                                                  notrend=1
                                                                                  # tweet_id=status.id
                                                                                  )
                                            # print("trend obj: ",trends_object.id, trends_object, trends_object.notrend)
                                            trends_object_list.append(trends_object)
                                            trends_object_list_text.append(ngram)
                                        elif ngram in trends_object_list_text:
                                            # print("ngram: ",ngram)
                                            for tmp in trends_object_list:
                                                if ngram == str(tmp):
                                                    count = tmp.notrend + 1
                                                    Trends.objects.filter(id=tmp.id).update(notrend=count)
                                # extract kg
                                triple_list = knowledge_graph_extract.extract_entity(text, nlp)
                                old_unique_knowledge = Unique_knowledge.objects.filter(keyword=keyword_obj)
                                old_unique_knowledge_text = []
                                for tmp in old_unique_knowledge:
                                    old_unique_knowledge_text.append(str(tmp))
                                for triple in triple_list:
                                    if len(triple) == 5:
                                        try:
                                            # db_knowledge_subj = dbpedia_query.check_link_DBpedia(triple[0])
                                            # db_knowledge_obj = dbpedia_query.check_link_DBpedia(triple[2])
                                            # if db_knowledge_subj:
                                            #     check_subj = 'true'
                                            # else:
                                            #     check_subj = 'false'
                                            # if db_knowledge_obj:
                                            #     check_obj = 'true'
                                            # else:
                                            #     check_obj = 'false'
                                            # check = check_subj + '-' + check_obj
                                            # print(check)
                                            Knowledge.objects.create(tweet=tweet_obj,
                                                                     keyword=keyword_obj,
                                                                     k_subject=triple[0],
                                                                     k_predicate=triple[1],
                                                                     k_object=triple[2],
                                                                     subject_type=triple[3],
                                                                     object_type=triple[4],
                                                                     is_new_knowledge="")
                                            tmp_knowledge = triple[0] + ', ' + triple[1] + ', ' + triple[2]
                                            if tmp_knowledge not in old_unique_knowledge_text:
                                                old_unique_knowledge_text.append(tmp_knowledge)
                                                Unique_knowledge.object.create(keyword=keyword_obj,
                                                                        k_subject=triple[0],
                                                                        k_predicate=triple[1],
                                                                        k_object=triple[2]
                                                                        )
                                        except:
                                            continue
                self.q.task_done()
            except Exception as e:
                print("save tweet error ", e)
        # except Exception as e:
        #     # print("raw data", raw_data)
        #     # self.q.put(raw_data)
        #     print("save_tweets error", e)


def on_limit(self, track):
    print("Rate Limit Exceeded, Sleep for 5 Mins")
    time.sleep(5 * 60)
    return True


def stop_streaming(self):
    id_list = []

    for keyword_obj in self.keyword_obj_list:
        id_list.append(keyword_obj.id)

    new_keyword_list = Keyword.objects.filter(pk__in=id_list)

    # stop streaming if user force stop
    stop_stream = False
    for keyword_obj in new_keyword_list:
        if keyword_obj.is_forced_stop:
            stop_stream = True
            break

    if stop_stream:
        for keyword_obj in new_keyword_list:
            keyword_obj.end_date = timezone.now()
            keyword_obj.is_streaming = False
            keyword_obj.save()

        self.used_token.used_count -= 1
        self.used_token.save()
        return False
    else:
        return True

    # stop streaming if timeout
    if timezone.now() < self.end_date:
        return True
    else:
        for keyword_obj in new_keyword_list:
            keyword_obj.end_date = timezone.now()
            keyword_obj.is_streaming = False
            keyword_obj.save()

        self.used_token.used_count -= 1
        self.used_token.save()
        return False


def on_error(self, status_code):
    print('Encountered streaming error (', status_code, ')')
    for keyword_obj in self.keyword_obj_list:
        keyword_obj.end_date = timezone.now()
        # keyword_obj.is_streaming = False
        keyword_obj.error_code = status_code
        keyword_obj.save()

    return False
    # if status_code == 420 or status_code == 401:
    #     return False
    # else:
    #     return True


def stream_search(keyword_obj_list, used_token, nlp):
    keywords = set()
    for keyword_obj in keyword_obj_list:
        keywords.add(keyword_obj.keyword)

    used_token.used_count += 1
    used_token.save()

    auth = tweepy.OAuthHandler(used_token.consumer_key, used_token.consumer_secret)
    auth.set_access_token(used_token.access_token, used_token.access_token_secret)

    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

    # stream_time_limit = 1 * 60 # 7 * 24 * 60 * 60
    try:
        streamListener = StreamListener(keyword_obj_list, used_token, nlp)
        stream = tweepy.Stream(auth=api.auth, listener=streamListener, tweet_mode='extended')
    except Exception as e:
        print("First exception ", e)
    print("Crawling keywords: ", keywords)
    try:
        stream.filter(track=keywords, is_async=True)
        return stream

    except Exception as e:
        print("exception stream ", e)
        return stream
