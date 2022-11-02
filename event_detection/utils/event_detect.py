import pandas as pd
import numpy as np
# import burst_detection as bd
from event_detection.utils import burst_detection as bd
from event_detection.utils import datetime_utils
from event_detection.utils import utils, text_utils
from event_detection.models import Events, Keyword, Tweet, Trends
from datetimerange import DateTimeRange
import datetime as dt
import collections
from datetime import datetime, timedelta


def tweets_distribution_countries(start_date, end_date, tweets_list, trend):
    x_data_date_group = []
    y_data_group = []
    time_range = DateTimeRange(start_date, end_date)
    time = []
    for value in time_range.range(dt.timedelta(hours=1)):
        time.append(value.strftime("%Y-%m-%d %H:%M"))
    time_option = "hour"
    for tweets in tweets_list:
        y_data_final = [0] * len(time)
        x_data_date, y_data = get_tweet_distribution(tweets, time_option, trend)
        for x in time:
            for x_date in x_data_date:
                if x == x_date:
                    y_data_final[time.index(x)] = y_data[x_data_date.index(x_date)]
        x_data_date_group.append(time)
        y_data_group.append(y_data_final)
    return x_data_date_group, y_data_group


def get_diffuse_degree(tweet_list, time_option):
    if time_option == 'second':  # minute
        pivot = 0
    elif time_option == 'minute':  # hour
        pivot = 3
    elif time_option == 'hour':  # day
        pivot = 6
    elif time_option == 'day':  # month
        pivot = 9
    else:
        pivot = 0
    counter = collections.Counter()
    if pivot == 0:
        for tweet in tweet_list:
            time = tweet['created_at'].strftime("%Y-%m-%d %H:%M:%S")
            counter.update([time])
    else:
        for tweet in tweet_list:
            time = tweet['created_at'].strftime("%Y-%m-%d %H:%M:%S")
            time = time[:-pivot]
            time_short = datetime_utils.correct_time(time)
            counter.update([time_short])
    counter_list = sorted(counter.items())
    x_data_date = [x for x, y in counter_list]
    y_data = [y for x, y in counter_list]

    return x_data_date, y_data


def get_tweet_distribution_kg(group_knowledge, time_option, keyword=None):
    if time_option == 'second':  # minute
        pivot = 0
    elif time_option == 'minute':  # hour
        pivot = 3
    elif time_option == 'hour':  # day
        pivot = 6
    elif time_option == 'day':  # month
        pivot = 9
    else:
        pivot = 0
    counter = collections.Counter()
    if pivot == 0:
        for knowledge in group_knowledge.iterator():
            # print("tweet ",tweet)
            if keyword is None or keyword.lower() in knowledge.tweet.text.lower():
                time = knowledge.tweet.created_at.strftime("%Y-%m-%d %H:%M:%S")
                counter.update([time])
    else:
        for knowledge in group_knowledge.iterator():
            # print("tweet ",tweet)
            if keyword is None or keyword.lower() in knowledge.tweet.text.lower():
                time = knowledge.tweet.created_at.strftime("%Y-%m-%d %H:%M:%S")
                time = time[:-pivot]
                time_short = datetime_utils.correct_time(time)
                counter.update([time_short])

    counter_list = sorted(counter.items())
    x_data_date = [x for x, y in counter_list]
    y_data = [y for x, y in counter_list]

    return x_data_date, y_data


def get_tweet_distribution(tweet_list, time_option, keyword):
    if time_option == 'second':  # minute
        pivot = 0
    elif time_option == 'minute':  # hour
        pivot = 3
    elif time_option == 'hour':  # day
        pivot = 6
    elif time_option == 'day':  # month
        pivot = 9
    else:
        pivot = 0
    counter = collections.Counter()
    keyword = keyword.lower()
    if pivot == 0:
        for tweet in tweet_list.iterator():
            # clean_text = text_utils.pre_process(tweet.text)
            # clean_text = clean_text.replace(".", ' ')
            # clean_text = tweet.text.replace(".", ' ')
            # clean_text = clean_text.strip()
            # clean_text = clean_text.lower()

            # print("tweet ",tweet)
            # if keyword is None or keyword.lower() in tweet.text.lower():  #for jananese
            if keyword is None or set(keyword.lower().split(" ")).issubset(set(tweet.text.lower().split(" "))): #for english
                time = tweet.created_at.strftime("%Y-%m-%d %H:%M:%S")
                counter.update([time])
    else:
        for tweet in tweet_list.iterator():
            # print("tweet ",tweet)
            # clean_text = text_utils.pre_process(tweet.text)
            # clean_text = clean_text.replace(".", ' ')
            # clean_text = clean_text.strip()
            # clean_text = clean_text.lower()
            if keyword == "":
                time = tweet.created_at.strftime("%Y-%m-%d %H:%M:%S")
                time = time[:-pivot]
                time_short = datetime_utils.correct_time(time)
                counter.update([time_short])
            else:
                if set(keyword.lower().split(" ")).issubset(set(tweet.text.lower().split(" "))):
                # if keyword is None or keyword.lower() in tweet.text.lower():
                    time = tweet.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    time = time[:-pivot]
                    time_short = datetime_utils.correct_time(time)
                    counter.update([time_short])

    counter_list = sorted(counter.items())
    x_data_date = [x for x, y in counter_list]
    y_data = [y for x, y in counter_list]

    return x_data_date, y_data

def get_tweet_distribution_countries_event(tweets_list, trend, countries):
    time = []
    for tweets in tweets_list:
        for tweet in tweets:
            time.append(tweet.created_at)
    start_date = datetime_utils.correct_time(min(time).strftime("%Y-%m-%d %H"))
    end_date = datetime_utils.correct_time(max(time).strftime("%Y-%m-%d %H"))
    time_range = DateTimeRange(start_date, end_date)
    time = []
    for value in time_range.range(dt.timedelta(hours=1)):
        time.append(value.strftime("%Y-%m-%d %H:%M"))
    y_data_final = [0] * len(time)

    x_data_date_group, y_data_group = tweets_distribution_countries(start_date, end_date, tweets_list, trend="")

    x_data_date_event, y_data_event = tweets_distribution_countries(start_date, end_date, tweets_list, trend=trend)
    y_proportion_group = []
    for i in range(len(countries)):
        y_proportion = []
        for index in range(len(y_data_group[i])):
            if y_data_group[i][index] != 0:
                tmp = y_data_event[i][index] / y_data_group[i][index]
            else:
                tmp = 0
            if tmp > 1:
                print(trend, countries[i], x_data_date_event[i][index], y_data_event[i][index], y_data_group[i][index])
            y_proportion.append(tmp)
        y_proportion_group.append(y_proportion)

    return x_data_date_event, y_proportion_group

def get_tweet_distribution_event(tweet_list, keyword, time_option, keyword_id):
    keyword_obj = Keyword.objects.filter(id=keyword_id)[0]
    start_date = keyword_obj.search_date.strftime("%Y-%m-%d %H:%M")
    end_date = keyword_obj.end_date.strftime("%Y-%m-%d %H:%M")
    time_range = DateTimeRange(start_date, end_date)
    time = []
    for value in time_range.range(dt.timedelta(hours=1)):
        time.append(value.strftime("%Y-%m-%d %H:%M"))
    y_data_final = [0] * len(time)
    x_data_date, y_data = get_tweet_distribution(tweet_list, time_option, "")
    for x in time:
        for x_date in x_data_date:
            if x == x_date:
                y_data_final[time.index(x)] = y_data[x_data_date.index(x_date)]
    y_data_event_final = [0] * len(time)
    x_data_date_event, y_data_event = get_tweet_distribution(tweet_list, time_option, keyword)
    for x in time:
        for x_date in x_data_date_event:
            if x == x_date:
                y_data_event_final[time.index(x)] = y_data_event[x_data_date_event.index(x_date)]
    y_proportion = []
    for y_event, y in zip(y_data_event_final, y_data_final):
        y_proportion.append(y_event / y if y != 0 else 0)

    return time, y_data_event_final, y_data_final, y_proportion


def detect_event(r, d):
    r = pd.Series(np.array(r, dtype=float))
    d = pd.Series(np.array(d, dtype=float))

    r = r.mask(r == 0).fillna(1)
    d = d.mask(d == 0).fillna(1)
    n = len(r)

    variables = [[2.0, 0.5]]
    # variables = [[1.5, 1.0],
    #              [2.0, 1.0],
    #              [3.0, 1.0],
    #              [4.0, 1.0],
    #              [2.0, 0.5],
    #              [2.0, 1.0],
    #              [2.0, 2.0],
    #              [2.0, 3.0]]

    burst_list = []
    for v in variables:
        # try:
            q, _, _, p = bd.burst_detection(r, d, n, v[0], v[1], smooth_win=1)

            label = 's=' + str(v[0]) + ', g=' + str(v[1])

            bursts = bd.enumerate_bursts(q, label)
            bursts = bd.burst_weights(bursts, r, d, p)

            burst_list.append(bursts)
        # except:
        #     # print(e)
        #     continue
    return burst_list, variables


def auto_detect(keyword_obj):
    keyword_id = keyword_obj.id
    countries = keyword_obj.countries
    top_trends = utils.get_top_trend_countries(keyword_id, countries)
    tweet_list = Tweet.objects.filter(keyword_id=keyword_id)
    x_data_date, y_data = get_tweet_distribution(tweet_list, "hour", "")
    tmp_time = []
    for tweet in tweet_list:
        tmp_time.append(tweet.created_at)
    start_date = datetime_utils.correct_time(min(tmp_time).strftime("%Y-%m-%d %H"))
    end_date = datetime_utils.correct_time(max(tmp_time).strftime("%Y-%m-%d %H"))
    time_range = DateTimeRange(start_date, end_date)
    time = []
    for value in time_range.range(dt.timedelta(hours=1)):
        time.append(value.strftime("%Y-%m-%d %H:%M"))

    y_data_final = [0] * len(time)
    for x in time:
        for x_date in x_data_date:
            if x == x_date:
                y_data_final[time.index(x)] = y_data[x_data_date.index(x_date)]
    y_data_final_new = [element * 7 for element in y_data_final]

    for trend in top_trends:
        # country_index = top_trends_list.index(trends_list)
        trend_obj = Trends.objects.filter(keyword_id=keyword_id, trend=trend)[0]
        for i in (range(len(countries))):
            # burst_list, variables = event_detect.detect_event(trend_obj.y_data_event[index],
            #                                                   keyword_obj.y_data[index])
            try:

                y_data_event = [element * 7 for element in trend_obj.y_data_event[i]]

                burst_list, variables = detect_event(y_data_event, y_data_final_new)
            except:
                continue
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
                            Events.objects.create(keyword=keyword_obj,
                                                  begin_time=start_time,
                                                  end_time=end_time,
                                                  trend=trend,
                                                  country=countries[i])
