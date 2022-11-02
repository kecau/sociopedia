import collections
from datetimerange import DateTimeRange
from django.utils import timezone
from datetime import datetime, timedelta
from event_detection.models import Keyword, Tweet, Trends, TopicsDB
from event_detection.utils import utils
import plotly.graph_objs as go
from event_detection.utils import datetime_utils
from plotly.subplots import make_subplots

from plotly.offline import plot

def get_tweet_in_time_range_country_trend(pk, start_date, end_date, country, trend):
    if start_date is None or start_date == "" or start_date == "None":
        start_date = datetime.strptime("2022-01-01 00:00", "%Y-%m-%d %H:%M")
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M")

    if end_date is None or end_date == "" or end_date == "None":
        end_date = timezone.now()
    else:
        end_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M")

    tweet_list = Tweet.objects.filter(keyword=pk, country=country,
                                      created_at__range=[start_date, end_date],
                                      text__contains=trend)  # .values("text", "created_at")
    return tweet_list

def get_tweet_in_time_range_country(pk, start_date, end_date, country, trend=""):
    if start_date is None or start_date == "" or start_date == "None":
        start_date = datetime.strptime("2022-01-01 00:00", "%Y-%m-%d %H:%M")
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M")

    if end_date is None or end_date == "" or end_date == "None":
        end_date = timezone.now()
    else:
        end_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M")

    tweet_list = Tweet.objects.filter(keyword=pk, country=country, 
                                      created_at__range=[start_date, end_date],
                                      text__contains=trend)  # .values("text", "created_at")
    return tweet_list

def get_tweet_distribution(tweet_list, time_option, keyword=None):
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
        for tweet in tweet_list.iterator():
            # print("tweet ",tweet)
            if keyword is None or keyword.lower() in tweet.text.lower():
                time = tweet.created_at.strftime("%Y-%m-%d %H:%M:%S")
                counter.update([time])
    else:
        for tweet in tweet_list.iterator():
            # print("tweet ",tweet)
            if keyword is None or keyword.lower() in tweet.text.lower():
                time = tweet.created_at.strftime("%Y-%m-%d %H:%M:%S")
                time = time[:-pivot]
                time_short = datetime_utils.correct_time(time)
                counter.update([time_short])

    counter_list = sorted(counter.items())
    x_data_date = [x for x, y in counter_list]
    y_data = [y for x, y in counter_list]

    return x_data_date, y_data

def plot_distribution_countries(x_data_date_group, y_data_group, countries):
    # fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig = go.Figure()
    for i in range(len(countries)):
        fig.add_trace(go.Scatter(x=x_data_date_group[i], y=y_data_group[i], mode='lines', name=countries[i]))
    fig.update_layout(
        xaxis=dict(
            title='Time',
            type='date'
        ),
        yaxis=dict(
            title='#Tweets'
        ),
        title='Tweets distribution by countries',
        legend_title="Countries:",
        paper_bgcolor="white"
    )
    # for event in events:
    #     index = events.index(event)
    #     text = "Event " + str(index + 1) + ": " + "<br>" + event[0] + '-' + event[1]
    #     fig.add_vrect(
    #             x0=event[0], x1=event[1],
    #             annotation_text='<i>' + text + '</i>',
    #             annotation_position="top left",
    #             fillcolor="#d2b0e0",
    #             opacity=0.5,
    #             layer="below", line_width=0,
    #     )
    # fig.show()
    plot_div = plot(fig,
                    output_type='div',
                    include_plotlyjs=False,
                    show_link=False,
                    link_text="")
    # print('plot_div ', plot_div)
    return plot_div
