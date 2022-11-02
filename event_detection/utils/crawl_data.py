import threading
import snscrape.modules.twitter as sntwitter
import schedule
from event_detection.utils import knowledge_graph_extract, text_utils, utils, datetime_utils, dbpedia_query
from event_detection.utils import event_detect
from event_detection.models import Tweet, Keyword, TwitterToken, Knowledge, Trends, TopicsDB, Unique_knowledge
import tweepy
import collections


class Crawl_data(threading.Thread):
    def __init__(self, keyword, country, nlp):
        threading.Thread.__init__(self)
        self.keyword = keyword
        self.country = country
        self.nlp = nlp

    def run(self):
        crawl_data(self.keyword, self.country, self.nlp)


class Crawl_data_news(threading.Thread):
    def __init__(self, keyword, country, nlp, api, account):
        threading.Thread.__init__(self)
        self.keyword = keyword
        self.country = country
        self.nlp = nlp
        self.api = api
        self.account = account

    def run(self):
        crawl_data_news(self.keyword, self.country, self.nlp, self.api, self.account)


def crawl_data_news(keyword_obj, country, nlp, api, account):
    print("Starting crawl: ", str(keyword_obj), account)
    schedule.every().hour.do(event_detect.auto_detect, keyword_obj)
    schedule.every().day.at("12:00").do(knowledge_graph_extract.get_temporal_knowledge, keyword_obj)
    while True:
        for page in tweepy.Cursor(api.user_timeline, screen_name=account, count=200).pages(15):
            for tweet in page:
                if str(keyword_obj).lower() in tweet.text.lower():
                    tweet_check = Tweet.objects.filter(keyword=keyword_obj, tweet_id=tweet.id)
                    if len(list(tweet_check)) == 0:
                        original_tweet_id = str(tweet.id)
                        text = text_utils.pre_process(tweet.text)
                        sentences = text.split('.')
                        scores = text_utils.score_sentiment(str(keyword_obj), sentences, nlp)
                        result = text_utils.get_label(scores)
                        tweet_obj = Tweet.objects.create(
                            keyword=keyword_obj,
                            tweet_id=tweet.id,
                            text=tweet.text,
                            created_at=tweet.created_at,
                            retweet_count=tweet.retweet_count,
                            favorite_count=tweet.favorite_count,
                            original_tweet_id=original_tweet_id,
                            country=country,
                            label=result["label"],
                            score=result["score"]
                        )
                        # print("inserted!")
                        # extract ngram
                        ngrams = utils.extract_ngrams(text, nlp)
                        counter = collections.Counter(ngrams)
                        for ngram in ngrams:
                            if len(ngram.strip()) >= 3 and (ngram.isnumeric() == False):
                                check_ngram = Trends.objects.filter(keyword=keyword_obj, trend=ngram, country=country)
                                if len(check_ngram) == 0:
                                    Trends.objects.create(keyword=keyword_obj, trend=ngram, notrend=counter[ngram],
                                                          country=country)
                                else:
                                    count = check_ngram[0].notrend + counter[ngram]
                                    Trends.objects.filter(id=check_ngram[0].id).update(notrend=count)
                        # extract kg
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
                                    uniqe_check = Unique_knowledge.objects.filter(keyword=keyword_obj,
                                                                                  k_subject=triple[0],
                                                                                  k_predicate=triple[1],
                                                                                  k_object=triple[2])
                                    if len(uniqe_check) == 0:
                                        Unique_knowledge.object.create(keyword=keyword_obj,
                                                                       k_subject=triple[0],
                                                                       k_predicate=triple[1],
                                                                       k_object=triple[2]
                                                                       )
                                except:
                                    continue


def crawl_data(keyword_obj, country, nlp):
    print("Starting crawl ", country.country_name)
    try:
        # schedule.every().hour.do(event_detect.auto_detect,keyword_ev)
        schedule.every().hour.do(event_detect.auto_detect, keyword_obj)
        schedule.every().day.at("12:00").do(knowledge_graph_extract.get_temporal_knowledge, keyword_obj)

    except:
        print("detect error")
    while True:
        # try:
        query = str(keyword_obj).lower() + ' place:' + country.place_id
        status = sntwitter.TwitterSearchScraper(query).get_items()
        for i, tweet in enumerate(status):
            # tweet_id = str(tweet.id)
            tweet_check = Tweet.objects.filter(keyword=keyword_obj, tweet_id=tweet.id)
            # print("tweet_check ", len(list(tweet_check)))
            # cursor = tweet_col.find({"tweet_id": tweet_id})
            if len(list(tweet_check)) == 0:
                original_tweet_id = ""
                if tweet.retweetedTweet is not None:
                    original_tweet_id = str(tweet.retweetedTweet.id)

                if tweet.quotedTweet is not None:
                    original_tweet_id = str(tweet.quotedTweet.id)
                text = text_utils.pre_process(tweet.text)
                sentences = text.split('.')
                scores = text_utils.score_sentiment(str(keyword_obj), sentences, nlp)
                result = text_utils.get_label(scores)
                tweet_obj = Tweet.objects.create(
                    keyword=keyword_obj,
                    tweet_id=tweet.id,
                    text=tweet.content,
                    created_at=tweet.date,
                    retweet_count=tweet.retweetCount,
                    favorite_count=tweet.likeCount,
                    original_tweet_id=original_tweet_id,
                    country=country.country_name,
                    label=result["label"],
                    score=result["score"]
                )
                # print("inserted!")
                # extract ngram
                ngrams = utils.extract_ngrams(text, nlp)
                counter = collections.Counter(ngrams)
                for ngram in ngrams:
                    if len(ngram.strip()) >= 3 and (ngram.isnumeric() == False):
                        check_ngram = Trends.objects.filter(keyword=keyword_obj, trend=ngram,
                                                            country=country.country_name)
                        if len(check_ngram) == 0:
                            Trends.objects.create(keyword=keyword_obj, trend=ngram, notrend=counter[ngram],
                                                  country=country.country_name)
                        else:
                            count = check_ngram[0].notrend + counter[ngram]
                            Trends.objects.filter(id=check_ngram[0].id).update(notrend=count)
                # extract kg
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
                            uniqe_check = Unique_knowledge.objects.filter(keyword=keyword_obj,
                                                                          k_subject=triple[0],
                                                                          k_predicate=triple[1],
                                                                          k_object=triple[2])
                            if len(uniqe_check) == 0:
                                Unique_knowledge.object.create(keyword=keyword_obj,
                                                               k_subject=triple[0],
                                                               k_predicate=triple[1],
                                                               k_object=triple[2]
                                                               )
                        except:
                            continue
    # except:
    #     continue
    # except Exception as e:
    #     print('First exception:', e)

    # while True:


def stream_search(keyword_obj_list, countries, nlp):
    keywords = set()
    for keyword_obj in keyword_obj_list:
        keywords.add(keyword_obj.keyword)
    try:
        for country in countries:
            streamListener = Crawl_data(keyword_obj_list[0], country, nlp)
            streamListener.start()
        return True
    except:
        return False


def stream_news(keyword_obj_list, nlp, used_token):
    keywords = set()
    for keyword_obj in keyword_obj_list:
        keywords.add(keyword_obj.keyword)
    auth = tweepy.OAuthHandler(used_token.consumer_key, used_token.consumer_secret)
    auth.set_access_token(used_token.access_token, used_token.access_token_secret)
    # TwitterToken.objects.filter(id=used_token.id).update(token_check=True)
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
    account_list_china = ["globaltimesnews", "PDChina"]
    account_list_japan = ["The_Japan_News", "themainichi"]
    # account_list_japan = ["AJWasahi", "The_Japan_News", "themainichi"]
    account_list_usa = ["TIME", "WSJ", "washingtonpost", "nytimes", "CNN", "FoxNews", "cnnbrk", ]
    try:
        for account in account_list_china:
            country = "China"
            streamListener = Crawl_data_news(keyword_obj_list[0], country, nlp, api, account)
            streamListener.start()
        for account in account_list_japan:
            country = "Japan"
            streamListener = Crawl_data_news(keyword_obj_list[0], country, nlp, api, account)
            streamListener.start()
        for account in account_list_usa:
            country = "United States"
            streamListener = Crawl_data_news(keyword_obj_list[0], country, nlp, api, account)
            streamListener.start()
        return True
    except Exception as e:
        print('Exception:', e)
        # TwitterToken.objects.filter(id=used_token.id).update(token_check=False)
        return False
