import collections
from datetime import datetime, timedelta
import datetime as dt
from tqdm import tqdm
from scipy import signal
import numpy as np
from plotly.offline import plot
# import plotly.graph_objs as go
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetimerange import DateTimeRange
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from event_detection.models import Keyword, Tweet, Trends, TopicsDB
from event_detection.utils import text_utils, knowledge_graph_extract, event_detect, dbpedia_query
from wordcloud import WordCloud
from collections import Counter
import plotly.figure_factory as ff
from nltk.corpus import stopwords
# import collections
# import string
# import re
# import nltk
from nltk.util import ngrams
# from scipy.fft import fft, ifft
from scipy.fft import rfft, rfftfreq, fftfreq
import random
from event_detection.utils import color_process


# nltk.download('punkt')


def get_tweet_in_time_range_countries(pk, start_date, end_date, countries, trend):
    if start_date is None or start_date == "" or start_date == "None":
        start_date = datetime.strptime("2022-01-01 00:00", "%Y-%m-%d %H:%M")
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M")

    if end_date is None or end_date == "" or end_date == "None":
        end_date = timezone.now()
    else:
        end_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M")
    tweets_list = []
    for country in countries:
        tweets = Tweet.objects.filter(keyword=pk, country=country,
                                      created_at__range=[start_date, end_date],
                                      text__contains=trend)
        tweets_list.append(tweets)
    return tweets_list


def get_tweet_sentiment_countries(pk, countries, label, start_date, end_date):
    if start_date is None or start_date == "" or start_date == "None":
        start_date = datetime.strptime("2022-01-01 00:00", "%Y-%m-%d %H:%M")
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M")

    if end_date is None or end_date == "" or end_date == "None":
        end_date = timezone.now()
    else:
        end_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M")
    tweets_list = []
    # print("check ", start_date, end_date)
    for country in countries:
        tweets = Tweet.objects.filter(keyword=pk, country=country, created_at__range=[start_date, end_date],
                                      label=label)
        tweets_list.append(tweets)
    return tweets_list


def plot_distribution_countries(x_data_date_group, y_data_group, countries):
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
    plot_div = plot(fig,
                    output_type='div',
                    include_plotlyjs=False,
                    show_link=False,
                    link_text="")
    # print('plot_div ', plot_div)
    return plot_div


def plot_distribution(tweet_list, time_option):
    # print(time_option)
    x_data_date, y_data = event_detect.get_tweet_distribution(tweet_list, time_option)
    # print(x_data_date,y_data)
    fig = go.Figure()
    if len(y_data) < 2:
        bar = go.Bar(x=x_data_date, y=y_data)
    else:
        bar = go.Scatter(x=x_data_date, y=y_data, mode='lines+markers')
    fig.add_trace(bar)
    fig.update_layout(
        xaxis=dict(
            title='Time',
            type='date'
        ),
        yaxis=dict(
            title='Number of tweets'
        ),
        title='Tweets Distribution'
    )

    plot_div = plot(fig,
                    output_type='div',
                    include_plotlyjs=False,
                    show_link=False,
                    link_text="")
    # print('plot_div ', plot_div)
    return plot_div


def plot_sentiment_countries(countries, sentiment_data, trend, events):
    df = pd.DataFrame(sentiment_data['x_data_date'][0], columns=["Time"])
    df = df.set_index("Time")
    maps = {}
    for i in range(len(countries)):
        tmp_pos = countries[i] + "_positive"
        tmp_neu = countries[i] + "_neutral"
        tmp_neg = countries[i] + "_negative"
        df[tmp_pos] = sentiment_data["positive"][i]
        df[tmp_neu] = sentiment_data["neutral"][i]
        df[tmp_neg] = sentiment_data["negative"][i]
        maps[countries[i]] = [tmp_pos, tmp_neu, tmp_neg]

    fig = px.line(df, x=df.index,
                  y=df.columns,
                  title='Sentiment distribution with trend: "' + trend + '" by countries', symbol='variable',
                  labels={
                      'value': "#tweets",
                      'variable': "Sentiment",
                  }
                  )

    group = []
    vis = []
    visList = []
    for m in maps.keys():
        for col in df.columns:
            if col in maps[m]:
                vis.append(True)
            else:
                vis.append(False)
        group.append(m)
        visList.append(vis)
        vis = []
    # print(visList)
    # buttons for each group
    buttons = []
    for i, g in enumerate(group):
        button = dict(label=g,
                      method='restyle',
                      args=['visible', visList[i]])
        buttons.append(button)
    # print(buttons)
    visible = np.array(["True" for _ in range(len(countries))])
    buttons = [{'label': 'all',
                'method': 'restyle',
                'args': ['visible', visible]}] + buttons
    fig.update_layout(
        updatemenus=[
            dict(
                type="dropdown",
                direction="down",
                buttons=buttons)
        ],
    )
    for event in events:
        index = events.index(event)
        color = color_process.getBGRandomColor(index)
        text = "Event " + str(index + 1)
        fig.add_vrect(
            x0=event[0], x1=event[1],
            annotation_text='<i>' + text + '</i>',
            annotation_position="top left",
            fillcolor=color, opacity=0.5,
            layer="below", line_width=0,
        ),
    plot_div = plot(fig,
                    output_type='div',
                    include_plotlyjs=False,
                    show_link=False,
                    link_text="")
    # print('plot_div ', plot_div)
    return plot_div


def plot_proportion_countries(x_data_date_group, y_proportion_group, countries, events, trend):
    fig = go.Figure()
    for i in range(len(countries)):
        fig.add_trace(go.Scatter(x=x_data_date_group[i], y=y_proportion_group[i], mode='lines', name=countries[i]))
    fig.update_layout(
        xaxis=dict(
            title='Time',
            type='date'
        ),
        yaxis=dict(
            title='Tweets proportion'
        ),
        title='Proportion of tweets which interests to trend: "' + trend + '" by countries ',
        legend_title="Countries:",
        paper_bgcolor="white"
    )
    for event in events:
        index = events.index(event)
        color = color_process.getBGRandomColor(index)
        text = "Event " + str(index + 1)
        fig.add_vrect(
            x0=event[0], x1=event[1],
            annotation_text='<i>' + text + '</i>',
            annotation_position="top left",
            fillcolor=color, opacity=0.5,
            layer="below", line_width=0,
        ),

    plot_div = plot(fig,
                    output_type='div',
                    include_plotlyjs=False,
                    show_link=False,
                    link_text="")
    # print('plot_div ', plot_div)
    return plot_div


def plot_distribution_event(x_data_date, y_data_event, y_proportion):
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    bar_1 = go.Scatter(x=x_data_date, y=y_proportion, mode='lines', name="tweet proportion")
    bar_2 = go.Scatter(x=x_data_date, y=y_data_event, mode='lines', name="number of tweets")
    fig.add_trace(bar_1, secondary_y=False)
    fig.add_trace(bar_2, secondary_y=True)

    fig.update_layout(
        xaxis=dict(
            title='Time',
            type='date'
        ),
        title='Tweets Distribution'
    )

    fig.update_yaxes(title_text="Tweet proportion", secondary_y=False)
    fig.update_yaxes(title_text="Number of tweets", secondary_y=True)

    plot_div = plot(fig,
                    output_type='div',
                    include_plotlyjs=False,
                    show_link=False,
                    link_text="")

    return plot_div


def plot_burst_timeline(x_data_date, burst_list, variables):
    fig = go.Figure()

    for i, bursts in enumerate(burst_list):
        label = 's=' + str(variables[i][0]) + ', g=' + str(variables[i][1])
        fig.add_trace(go.Scatter(x=x_data_date, y=[i] * len(x_data_date), mode='markers', marker=dict(size=5, color=1),
                                 name=label))
        for index, burst in bursts.iterrows():
            start = burst['begin']
            end = burst['end']

            fig.add_trace(go.Scatter(
                x=[x_data_date[start], x_data_date[start], x_data_date[end], x_data_date[end], x_data_date[start]],
                y=[i - 0.2, i + 0.2, i + 0.2, i - 0.2, i - 0.2],
                fill="toself",
                marker=dict(size=5, color=4),
                marker_color='rgba(0, 0, 0, .8)',
                showlegend=False))

    plot_div = plot(fig,
                    output_type='div',
                    include_plotlyjs=False,
                    show_link=False,
                    link_text="")

    return plot_div


def plot_timeline_visual(knowledgegraph):
    data = []
    colors = []
    for i in range(len(knowledgegraph)):
        if knowledgegraph[i] != []:
            for row in knowledgegraph[i]:
                if row['time_start'] != row['time_end']:
                    data.append({
                        "Task": row["subject"] + ' ' + row['predicate'] + ' ' + row['object'],
                        "Start": row['time_start'],
                        "Finish": row['time_end'],
                        "Resource": 'Event ' + str(i + 1)
                    })
        color = color_process.getNewRandomColor(i)
        colors.append(color)
    fig = ff.create_gantt(data, colors=colors, index_col='Resource', show_colorbar=True, group_tasks=True)
    # fig = px.timeline(data, color="Resource")
    fig.update_layout(title='Timeline visualization')
    plot_div = plot(fig,
                    output_type='div',
                    include_plotlyjs=False,
                    show_link=False,
                    link_text="")

    return plot_div


def get_presened_knowledge(knowledgegraph):
    max_mention = 0
    present_knowledge = ""
    no_country = 0
    for knowledge in knowledgegraph:
        if knowledge["mentions"] > max_mention:
            max_mention = knowledge["mentions"]
            present_knowledge = "{" + knowledge["subject"] + ", " + knowledge["predicate"] + ", " + knowledge[
                "object"] + "}"
            for row in knowledge["country"]:
                no_country += len(row)
        if knowledge["mentions"] == max_mention:
            if len(knowledge["country"]) > no_country:
                max_mention = knowledge["mentions"]
                present_knowledge = "{" + knowledge["subject"] + ", " + knowledge["predicate"] + ", " + knowledge[
                    "object"] + "}"
                for row in knowledge["country"]:
                    no_country += len(row)
    return present_knowledge


def plot_event_timeline(knowledgegraphs, events):
    df = []
    colors = []
    for event in events:
        tmp = {}
        tmp["Event"] = "Event " + str(events.index(event) + 1)
        # tmp["Event"] = events.index(event) + 1
        tmp["Start time"] = event[0]
        tmp["End time"] = event[1]
        tmp["Present Knowledge"] = get_presened_knowledge(knowledgegraphs[events.index(event)])
        df.append(tmp)
        color = color_process.getNewRandomColor(events.index(event))
        colors.append(color)
    fig = px.timeline(df, title='Event distribution over time', x_start="Start time", x_end="End time",
                      y="Event", hover_name="Present Knowledge",
                      color="Event", color_discrete_sequence=colors)
    fig.update_layout(xaxis_showgrid=True, yaxis_showgrid=True)
    plot_div = plot(fig,
                    output_type='div',
                    include_plotlyjs=False,
                    show_link=False,
                    link_text="")

    return plot_div


def plot_event_timeline_chart(knowledgegraphs, events):
    noCols = 2
    noRows = (len(knowledgegraphs) - 1) // 2 + 1
    specs = []
    for i in range(len(knowledgegraphs)):
        tmp = [{'type': 'domain'}, {'type': 'domain'}]
        specs.append({'type': 'domain'})
    fig = make_subplots(rows=1, cols=len(knowledgegraphs), specs=[specs])

    for i in range(len(knowledgegraphs)):
        event = "Event " + str(i + 1)
        ids = [event]
        labels = [event]
        parents = [""]
        values = [0]
        datasetSentiment = {}
        tmp = []
        for knowledge in knowledgegraphs[i]:
            for row in knowledge["country"]:
                for country in row:
                    tmp_check = {
                        "noNeu": 0,
                        "noPos": 0,
                        "noNeg": 0,
                    }
                    if country not in tmp:
                        tmp.append(country)
                        tmp_check["noTweets"] = 1
                        if knowledge["label"][knowledge["country"].index(row)][row.index(country)] == "neutral":
                            tmp_check["noNeu"] = 1
                        if knowledge["label"][knowledge["country"].index(row)][row.index(country)] == "positive":
                            tmp_check["noPos"] = 1
                        if knowledge["label"][knowledge["country"].index(row)][row.index(country)] == "negative":
                            tmp_check["noNeg"] = 1
                        datasetSentiment[country] = tmp_check
                    else:
                        datasetSentiment[country]["noTweets"] += 1
                        if knowledge["label"][knowledge["country"].index(row)][row.index(country)] == "neutral":
                            datasetSentiment[country]["noNeu"] += 1
                        if knowledge["label"][knowledge["country"].index(row)][row.index(country)] == "positive":
                            datasetSentiment[country]["noPos"] += 1
                        if knowledge["label"][knowledge["country"].index(row)][row.index(country)] == "negative":
                            datasetSentiment[country]["noNeg"] += 1

        for element in list(datasetSentiment.items()):
            ids.append(element[0])
            labels.append(element[0])
            parents.append(event)
            values.append(element[1]["noTweets"])
            if element[1]["noNeu"] != 0:
                id = element[0] + "-" + "neu"
                ids.append(id)
                labels.append("Neutral")
                parents.append(element[0])
                values.append(element[1]["noNeu"])
            if element[1]["noPos"] != 0:
                id = element[0] + "-" + "pos"
                ids.append(id)
                labels.append("Positive")
                parents.append(element[0])
                values.append(element[1]["noPos"])
            if element[1]["noNeg"] != 0:
                id = element[0] + "-" + "neg"
                ids.append(id)
                labels.append("Negative")
                parents.append(element[0])
                values.append(element[1]["noNeg"])
        colors = [''] * len(ids)
        for index in range(len(colors)):
            colors[index] = color_process.getNewRandomColor(index)
            if labels[index] == "Positive":
                colors[index] = "#2b78e4"
            if labels[index] == "Negative":
                colors[index] = "#cc0000"
            if labels[index] == "Neutral":
                colors[index] = "#ff9900"
        colors[0] = "#FFFFF"
        fig.add_trace((go.Sunburst(
            ids=ids,
            labels=labels,
            parents=parents,
            values=values,
            marker=dict(colors=colors),
            name='Event ' + str(i + 1)
        # )), row=i // 2 + 1, col=(i % 2) + 1)
        )), row=1, col=i+1)
        fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))
        fig.update_traces(hovertemplate=(
                '<br><b>%{parent}</b><br>' + '<br><b>%{label}</b><br>' + '<br><b>No.of tweets</b>: %{value}<br>'))
    plot_div = plot(fig,
                    output_type='div',
                    include_plotlyjs=False,
                    show_link=False,
                    link_text="")

    return plot_div

def split(arr, size):
    arrs = []
    while len(arr) > size:
        pice = arr[:size]
        arrs.append(pice)
        arr = arr[size:]
    arrs.append(arr)
    return arrs


def plot_characteristics(knowledgegraph, max_len):
    xf = rfftfreq(max_len, 1)
    df_occurrence_frequency = pd.DataFrame(xf.real, columns=["Frequency"])
    df_diffuse_degree_frequency = pd.DataFrame(xf.real, columns=["Frequency"])
    df_occurrence_frequency = df_occurrence_frequency.set_index("Frequency")
    df_diffuse_degree_frequency = df_diffuse_degree_frequency.set_index("Frequency")
    df_occurrence_psd = pd.DataFrame(columns=["Frequency"])
    df_diffuse_degree_psd = pd.DataFrame(columns=["Frequency"])
    maps = {}
    for i in range(len(knowledgegraph)):
        group_spo = []
        for element in knowledgegraph[i]:
            spo = element['subject'] + " " + element['predicate'] + " " + element['object']
            group_spo.append(spo)

            # occurrence = element['occurrence']
            # tmp_occurrence = split(occurrence, 60)
            # occurrence_hour = []
            # for unit in tmp_occurrence:
            #     occurrence_hour.append(sum(unit))

            # diffuse_degree = element['diffuse_degree']
            # tmp_diffuse_degree = split(diffuse_degree, 60)
            # diffuse_degree_hour = []
            # for unit in tmp_diffuse_degree:
            #     diffuse_degree_hour.append(sum(unit))

            occurrence = rfft(element['occurrence'])
            # occurrence = rfft(occurrence_hour)

            df_occurrence_frequency[spo] = occurrence.real

            diffuse_degree = rfft(element['diffuse_degree'])
            # diffuse_degree = rfft(diffuse_degree_hour)
            df_diffuse_degree_frequency[spo] = diffuse_degree.real

            freqs_occurrence, psd_occurrence = signal.periodogram(occurrence, fs=0.3)
            freqs_occurrence = np.array(freqs_occurrence)
            freqs_diffuse_degree, psd_diffuse_degree = signal.periodogram(diffuse_degree, fs=0.3)
            freqs_diffuse_degree = np.array(freqs_diffuse_degree)

            df_occurrence_psd["Frequency"] = freqs_occurrence.real
            df_occurrence_psd[spo] = psd_occurrence.real

            df_diffuse_degree_psd["Frequency"] = freqs_diffuse_degree.real
            df_diffuse_degree_psd[spo] = psd_diffuse_degree.real

        maps["Event " + str(i + 1) + " (" + str(len(group_spo)) + ")"] = group_spo

    df_occurrence_psd = df_occurrence_psd.set_index("Frequency")
    df_diffuse_degree_psd = df_diffuse_degree_psd.set_index("Frequency")

    fig_occurrence_frequency = px.line(df_occurrence_frequency, x=df_occurrence_frequency.index,
                                       y=df_occurrence_frequency.columns,
                                       title="SPOs occurrence in frequency-domain", symbol='variable',
                                       labels={
                                           'value': "Occurrence",
                                           'variable': "SPOs",
                                       }
                                       )
    fig_diffuse_degree_frequency = px.line(df_diffuse_degree_frequency, x=df_diffuse_degree_frequency.index,
                                           y=df_diffuse_degree_frequency.columns,
                                           title="SPOs diffuse-degree in frequency-domain", symbol='variable',
                                           labels={
                                               'value': "Diffuse_degree",
                                               'variable': "SPOs",
                                           }
                                           )
    fig_occurrence_psd = px.line(df_occurrence_psd, x=df_occurrence_psd.index, y=df_occurrence_psd.columns,
                                 title="Power spectral density of SPOs occurrence in frequency-domain",
                                 symbol='variable',
                                 labels={
                                     'value': "Psd",
                                     'variable': "SPOs",
                                 }
                                 )
    fig_diffuse_degree_psd = px.line(df_diffuse_degree_psd, x=df_diffuse_degree_psd.index,
                                     y=df_diffuse_degree_psd.columns,
                                     title="Power spectral density of SPOs diffuse-degree in frequency-domain",
                                     symbol='variable',
                                     labels={
                                         'value': "Psd",
                                         'variable': "SPOs",
                                     }
                                     )
    group = []
    vis = []
    visList = []
    for m in maps.keys():
        for col in df_occurrence_frequency.columns:
            if col in maps[m]:
                vis.append(True)
            else:
                vis.append(False)
        group.append(m)
        visList.append(vis)
        vis = []
    # print(visList)
    # buttons for each group
    buttons = []
    for i, g in enumerate(group):
        button = dict(label=g,
                      method='restyle',
                      args=['visible', visList[i]])
        buttons.append(button)
    # print(buttons)
    visible = np.array(["True" for _ in range(len(knowledgegraph))])
    buttons = [{'label': 'all',
                'method': 'restyle',
                'args': ['visible', visible]}] + buttons

    fig_occurrence_frequency.update_layout(
        updatemenus=[
            dict(
                type="dropdown",
                direction="down",
                buttons=buttons)
        ],
    )
    fig_diffuse_degree_frequency.update_layout(
        updatemenus=[
            dict(
                type="dropdown",
                direction="down",
                buttons=buttons)
        ],
    )
    fig_occurrence_psd.update_layout(
        updatemenus=[
            dict(
                type="dropdown",
                direction="down",
                buttons=buttons)
        ],
    )
    fig_diffuse_degree_psd.update_layout(
        updatemenus=[
            dict(
                type="dropdown",
                direction="down",
                buttons=buttons)
        ],
    )
    plot_div_occurrence_frequency = plot(fig_occurrence_frequency,
                                         output_type='div',
                                         include_plotlyjs=False,
                                         show_link=False,
                                         link_text="")
    plot_div_diffuse_degree_frequency = plot(fig_diffuse_degree_frequency,
                                             output_type='div',
                                             include_plotlyjs=False,
                                             show_link=False,
                                             link_text="")
    plot_div_occurrence_psd = plot(fig_occurrence_psd,
                                   output_type='div',
                                   include_plotlyjs=False,
                                   show_link=False,
                                   link_text="")
    plot_div_diffuse_degree_psd = plot(fig_diffuse_degree_psd,
                                       output_type='div',
                                       include_plotlyjs=False,
                                       show_link=False,
                                       link_text="")
    return plot_div_occurrence_frequency, plot_div_diffuse_degree_frequency, plot_div_occurrence_psd, plot_div_diffuse_degree_psd


def plot_characteristics_time(knowledgegraph, events, start_date, end_date):
    time_range = DateTimeRange(start_date, end_date)
    time = []
    # for value in time_range.range(dt.timedelta(hours=1)):
    for value in time_range.range(dt.timedelta(hours=1)):
        time.append(value.strftime("%Y-%m-%d %H:%M"))
    maps = {}

    df_occurrence = pd.DataFrame(time, columns=["Time"])
    df_diffuse_degree = pd.DataFrame(time, columns=["Time"])
    for i in range(len(knowledgegraph)):
        group_spo = []
        for element in knowledgegraph[i]:
            spo = element['subject'] + " " + element['predicate'] + " " + element['object']
            group_spo.append(spo)
            occurrence = element['occurrence']
            # tmp_occurence = split(occurrence, 60)
            # # print(len(occurrence))
            # occurrence_hour = []
            # for unit in tmp_occurence:
            #     occurrence_hour.append(sum(unit))

            diffuse_degree = element['diffuse_degree']
            # tmp_diffuse_degree = split(diffuse_degree, 60)
            # diffuse_degree_hour = []
            # for unit in tmp_diffuse_degree:
            #     diffuse_degree_hour.append(sum(unit))
            # print("occurrence_hour ", len(occurrence_hour))
            # df_occurrence[spo] = occurrence_hour
            # df_diffuse_degree[spo] = diffuse_degree_hour
            df_occurrence[spo] = occurrence
            df_diffuse_degree[spo] = diffuse_degree
        maps["Event " + str(i + 1) + " (" + str(len(group_spo)) + ")"] = group_spo
    df_occurrence = df_occurrence.set_index("Time")
    df_diffuse_degree = df_diffuse_degree.set_index("Time")
    fig_occurrence = px.line(df_occurrence, x=df_occurrence.index, y=df_occurrence.columns,
                             title="SPOs occurrence in time-domain",
                             symbol='variable',
                             labels={
                                 'value': "Occurrence",
                                 'variable': "SPOs",
                             }
                             )
    fig_diffuse_degree = px.line(df_diffuse_degree, x=df_diffuse_degree.index,
                                 y=df_diffuse_degree.columns,
                                 title="SPOs diffuse-degree in time-domain",
                                 symbol='variable',
                                 labels={
                                     'value': "Diffuse-Degree",
                                     'variable': "SPOs",
                                 }
                                 )
    group = []
    vis = []
    visList = []
    for m in maps.keys():
        for col in df_occurrence.columns:
            if col in maps[m]:
                vis.append(True)
            else:
                vis.append(False)
        group.append(m)
        visList.append(vis)
        vis = []
    # print(visList)
    # buttons for each group
    buttons = []
    for i, g in enumerate(group):
        button = dict(label=g,
                      method='restyle',
                      args=['visible', visList[i]])
        buttons.append(button)
    # print(buttons)
    visible = np.array(["True" for _ in range(len(knowledgegraph))])
    buttons = [{'label': 'all',
                'method': 'restyle',
                'args': ['visible', visible]}] + buttons

    fig_occurrence.update_layout(
        updatemenus=[
            dict(
                type="dropdown",
                direction="down",
                buttons=buttons)
        ],
    )
    fig_diffuse_degree.update_layout(
        updatemenus=[
            dict(
                type="dropdown",
                direction="down",
                buttons=buttons)
        ],
    )

    for event in events:
        index = events.index(event)
        color = color_process.getBGRandomColor(index)
        text = "Event " + str(index + 1) + ": " + "\n" + event[0] + '-' + event[1]
        if knowledgegraph[index] != []:
            fig_occurrence.add_vrect(
                x0=event[0], x1=event[1],
                annotation_text='<i>' + text + '</i>',
                annotation_position="top left",
                fillcolor=color, opacity=0.5,
                layer="below", line_width=0,
            ),
            fig_diffuse_degree.add_vrect(
                x0=event[0], x1=event[1],

                annotation_text='<i>' + text + '</i>',
                annotation_position="top left",
                fillcolor=color, opacity=0.5,
                layer="below", line_width=0,
            ),
        else:
            fig_occurrence.add_vrect(
                x0=event[0], x1=event[1],

                annotation_text=" ",
                annotation_position="top left",
                fillcolor=color, opacity=0.5,
                layer="below", line_width=0,
            ),
            fig_diffuse_degree.add_vrect(
                x0=event[0], x1=event[1],

                annotation_text=" ",
                annotation_position="top left",
                fillcolor=color, opacity=0.5,
                layer="below", line_width=0,
            ),

    plot_div_occurrence = plot(fig_occurrence,
                               output_type='div',
                               include_plotlyjs=False,
                               show_link=False,
                               link_text="")
    plot_div_diffuse_degree = plot(fig_diffuse_degree,
                                   output_type='div',
                                   include_plotlyjs=False,
                                   show_link=False,
                                   link_text="")
    return plot_div_occurrence, plot_div_diffuse_degree


def plot_timeline_knowledge(knowledgegraph, events, start_date, end_date):
    white = np.array([255, 255, 255])
    default_point = 10
    time_range = DateTimeRange(start_date, end_date)
    time = []
    for value in time_range.range(dt.timedelta(hours=1)):
        time.append(value.strftime("%Y-%m-%d %H:%M"))
    group_df = []
    default_y = 10
    count = 0
    for knowledge in tqdm(knowledgegraph):
        index_event = knowledgegraph.index(knowledge)
        time_range_event = DateTimeRange(events[index_event][0], events[index_event][1])
        time_event = []
        for value in time_range_event.range(dt.timedelta(hours=1)):
            time_event.append(value.strftime("%Y-%m-%d %H:%M"))
        for element in knowledge:
            count += 1
            x_axix = random.choice(time_event)
            tmp_list = {}
            spo = "(" + element['subject'] + ", " + element['predicate'] + ", " + element['object'] + ")"
            tmp_list["time"] = time
            tmp_list["time_valid"] = "[" + element['time_start'] + "-" + element['time_end'] + "]"
            tmp_list["spo"] = np.array([spo for _ in range(len(time))])
            tmp_list["event"] = "Event " + str(knowledgegraph.index(knowledge) + 1)
            tmp_list['x'] = np.array([x_axix for _ in range(len(time))])
            tmp_list['y'] = default_y + knowledge.index(element) * 5 + count
            occurrence = element['occurrence']
            # tmp_occurrence = split(occurrence, 60)
            # occurrence_hour = []
            # for unit in tmp_occurrence:
            #     occurrence_hour.append(sum(unit))

            diffuse_degree = element['diffuse_degree']
            # tmp_diffuse_degree = split(diffuse_degree, 60)
            # diffuse_degree_hour = []
            # for unit in tmp_diffuse_degree:
            #     diffuse_degree_hour.append(sum(unit))
            # tmp_list['occurrence'] = occurrence_hour
            # tmp_list['diffuse_degree'] = diffuse_degree_hour
            tmp_list['occurrence'] = occurrence
            tmp_list['diffuse_degree'] = diffuse_degree
            df = pd.DataFrame(tmp_list)
            df['size'] = df['occurrence'] + df['diffuse_degree'] + default_point
            group_df.append(df)
    dataset = pd.concat(group_df)

    # make figure
    fig_dict = {
        "data": [],
        "layout": {},
        "frames": []
    }

    fig_dict["layout"]["hovermode"] = "closest"
    fig_dict["layout"]["updatemenus"] = [
        {
            "buttons": [
                {
                    "args": [None, {"frame": {"duration": 500, "redraw": False},
                                    "fromcurrent": True, "transition": {"duration": 300,
                                                                        "easing": "quadratic-in-out"}}],
                    "label": "Play",
                    "method": "animate"
                },
                {
                    "args": [[None], {"frame": {"duration": 0, "redraw": False},
                                      "mode": "immediate",
                                      "transition": {"duration": 0}}],
                    "label": "Pause",
                    "method": "animate"
                }
            ],
            "direction": "left",
            "pad": {"r": 10, "t": 87},
            "showactive": False,
            "type": "buttons",
            "x": 0.1,
            "xanchor": "right",
            "y": 0,
            "yanchor": "top"
        }
    ]

    sliders_dict = {
        "active": 0,
        "yanchor": "top",
        "xanchor": "left",
        "currentvalue": {
            "font": {"size": 14},
            "prefix": "Time:",
            "visible": True,
            "xanchor": "right"
        },
        "transition": {"duration": 300, "easing": "cubic-in-out"},
        "pad": {"b": 10, "t": 50},
        "len": 0.9,
        "x": 0.1,
        "y": 0,
        "steps": []
    }

    # make data in default step
    default_step = time[0]
    dataset_by_time = dataset[dataset["time"] == default_step]

    for index, row in dataset_by_time.iterrows():
        spo = row['spo']
        x_axix = [row['x']]
        # x_axix = [default_step]
        y_axix = [row['y']]
        size = [row['size']]
        event = row['event']
        time_valid = row['time_valid']
        occurrence = row['occurrence']
        diffuse_degree = row['diffuse_degree']
        color = color_process.getNewRandomColor(int(row["event"].split(" ")[1]) - 1)
        rgb_color = np.array(color_process.hex_to_rgb(color))
        node_color = color_process.lerp(rgb_color, white, 1 / (size[0] + 1 / 0.55 - default_point))
        hex_color = color_process.rgb2hex(int(node_color[0]), int(node_color[1]), int(node_color[2]))

        data_dict = {
            "x": x_axix,
            "y": y_axix,
            "mode": "markers",
            "text": spo,
            "marker": {
                # "sizemode": "area",
                # "sizeref": 200000,
                "color": hex_color,
                "size": size,
            },
            "name": spo,
            "legendgroup": event,
            "legendgrouptitle_text": '<b>' + event + " (" + str(
                len(knowledgegraph[int(row["event"].split(" ")[1]) - 1])) + " knowledge): " + '</b>',
            "hovertemplate": f"SPO: {spo}<br>Valid time: {time_valid} </br>Occurrence: {occurrence} </br>Diffuse-degree: {diffuse_degree} </br>Event: {event} <extra></extra>",

        }
        fig_dict["data"].append(data_dict)
    # make frames
    node_color_list = []
    for value in tqdm(time):
        frame = {"data": [], "name": value}
        dataset_by_time = dataset[dataset["time"] == value]
        for index, row in dataset_by_time.iterrows():
            spo = row['spo']
            x_axix = [row['x']]
            # x_axix = [value]
            y_axix = [row['y']]
            size = [row['size']]
            event = row['event']
            time_valid = row['time_valid']
            occurrence = row['occurrence']
            diffuse_degree = row['diffuse_degree']
            color = color_process.getNewRandomColor(int(row["event"].split(" ")[1]) - 1)
            rgb_color = np.array(color_process.hex_to_rgb(color))
            node_color = color_process.lerp(rgb_color, white, 1 / (size[0] + 1 / 0.55 - default_point))
            hex_color = color_process.rgb2hex(int(node_color[0]), int(node_color[1]), int(node_color[2]))
            node_color_list.append(hex_color)
            data_dict = {
                "x": x_axix,
                "y": y_axix,
                "mode": "markers",
                "text": spo,
                "marker": {
                    # "sizemode": "area",
                    # "sizeref": 200000,
                    "color": hex_color,
                    "size": size,
                },
                "name": spo,
                "legendgroup": event,
                "legendgrouptitle_text": '<b>' + event + " (" + str(
                    len(knowledgegraph[int(row["event"].split(" ")[1]) - 1])) + " knowledge): " + '</b>',
                "hovertemplate": f"SPO: {spo}<br>Valid time: {time_valid} </br>Occurrence: {occurrence} </br>Diffuse-degree: {diffuse_degree} </br>Event: {event} <extra></extra>",

            }
            frame["data"].append(data_dict)
        fig_dict["frames"].append(frame)
        slider_step = {"args": [
            [value],
            {"frame": {"duration": 300, "redraw": False},
             "mode": "immediate",
             "transition": {"duration": 300}}
        ],
            "label": value,
            "method": "animate"}
        sliders_dict["steps"].append(slider_step)
    # print(node_color_list)
    fig_dict["layout"]["sliders"] = [sliders_dict]
    fig = go.Figure(fig_dict)
    fig.update_layout(legend=dict(groupclick="toggleitem"))
    fig.update_layout(legend={'itemsizing': 'constant'})
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)
    fig.update_layout(yaxis_visible=False, yaxis_showticklabels=False)

    for event in events:
        index = events.index(event)
        color = color_process.getBGRandomColor(index)
        text = "Event " + str(index + 1) + ": " + "\n" + event[0] + '-' + event[1]
        if knowledgegraph[index] != []:
            fig.add_vrect(
                x0=event[0], x1=event[1],
                annotation_text='<i>' + text + '</i>',
                annotation_position="top left",
                fillcolor=color, opacity=0.5,
                layer="below", line_width=0,
            ),
        else:
            fig.add_vrect(
                x0=event[0], x1=event[1],

                annotation_text=" ",
                annotation_position="top left",
                fillcolor=color, opacity=0.5,
                layer="below", line_width=0,
            ),
    plot_div = plot(fig,
                    output_type='div',
                    include_plotlyjs=True,
                    show_link=False,
                    link_text="")
    return plot_div


def plot_timeline(knowledgegraphs):
    df = []
    for knowledgegraph in knowledgegraphs:
        for knowledge in knowledgegraph:
            for i in range(len(knowledge["country"])):
                for country in knowledge["country"][i]:
                    tmp = {}
                    spo = "{" + knowledge["subject"] + ", " + knowledge["predicate"] + ", " + knowledge[
                        "object"] + "}"
                    tmp["Knowledge"] = spo
                    tmp["Country"] = country
                    tmp["Start time"] = knowledge["timeline"][i][0]
                    tmp["End time"] = knowledge["timeline"][i][1]
                    df.append(tmp)

    # df = pd.DataFrame(columns=["SPO", "Start", "Finish", "Country"])
    countries = []
    for knowledgegraph in knowledgegraphs:
        for knowledge in knowledgegraph:
            if knowledge["country"] not in countries:
                countries.append(knowledge["country"])
    #         spo = "(" + knowledge['subject'] + ", " + knowledge['predicate'] + ", " + knowledge['object'] + ")"
    #         for time in knowledge["timeline"]:
    #             # pd.concat((df, [{"SPO": spo, "Start": time[0], "Finish": time[1], "Country": knowledge['country'],
    #             #                 }]), axis=0)
    #             df = df.append({"SPO": spo, "Start": time[0], "Finish": time[1], "Country": knowledge['country'],
    #                             },
    #                            ignore_index=True)
    # # print(df)
    # # df.to_csv('timeout.csv', index=False)
    colors = []

    for index in range(len(countries)):
        colors.append(color_process.getNewRandomColor(index))
    fig = px.timeline(df, title='Temporal knowledge by countries', x_start="Start time", x_end="End time",
                      y="Knowledge",
                      color="Country", color_discrete_sequence=colors)
    # fig = px.bar(df, y="Country", x="pop", color="continent", orientation="h", hover_name="country",
    #              color_discrete_sequence=["red", "green", "blue", "goldenrod", "magenta"],
    #              title="Explicit color sequence"
    #              )
    # fig.show()
    fig.update_layout(xaxis_showgrid=True, yaxis_showgrid=True)
    fig.update_yaxes(autorange='reversed')
    for shape in fig['data']:
        shape['opacity'] = 0.7
    plot_div = plot(fig,
                    output_type='div',
                    include_plotlyjs=True,
                    show_link=False,
                    link_text="")
    return plot_div


def paging_tweets(tweet_list, page):
    tweet_per_page = 50
    tweet_index = [i + 1 for i in range((int(page) - 1) * tweet_per_page, int(page) * tweet_per_page)]
    paginator = Paginator(tweet_list, tweet_per_page)
    try:
        tweets = paginator.page(page)
    except PageNotAnInteger:
        tweets = paginator.page(1)
    except EmptyPage:
        tweets = paginator.page(paginator.num_pages)

    page_start = tweets.number - 2
    page_end = tweets.number + 3
    if page_start <= 0: page_start = 1
    if page_end > tweets.paginator.page_range[-1] + 1: page_end = tweets.paginator.page_range[-1] + 1

    page_range = list(range(page_start, page_end))
    if page_start > 2:
        page_range = [1, -1] + page_range
    elif page_start > 1:
        page_range = [1] + page_range
    if page_end < tweets.paginator.page_range[-1]:
        page_range = page_range + [-1, tweets.paginator.page_range[-1]]
    elif page_end < tweets.paginator.page_range[-1] + 1:
        page_range = page_range + [tweets.paginator.page_range[-1]]

    for tweet in tweets:
        # print(tweet[0].tweet_id)
        tweet.user_id = str(tweet.user_id)
        tweet.tweet_id = str(tweet.tweet_id)
        tweet.created_at_str = tweet.created_at.strftime("%Y/%m/%d, %H:%M:%S")

    return tweets, tweet_index, page_range


def get_tweet_in_time_range(pk, start_date, end_date, trend):
    if start_date is None or start_date == "" or start_date == "None":
        start_date = datetime.strptime("2022-01-01 00:00", "%Y-%m-%d %H:%M")
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M")

    if end_date is None or end_date == "" or end_date == "None":
        end_date = timezone.now()
    else:
        end_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M")

    tweet_list = Tweet.objects.filter(keyword=pk,
                                      created_at__range=[start_date, end_date],
                                      text__contains=trend)  # .values("text", "created_at")
    return tweet_list


def get_top_trend(pk):
    top_trends = []
    pk = int(pk)
    raw_trends = Trends.objects.raw(
        "SELECT 1 as id, trend FROM public.event_detection_trends WHERE keyword_id = '%s' ORDER BY notrend DESC LIMIT 10 ",
        [pk])
    for trend in raw_trends:
        top_trends.append(str(trend))
    return top_trends


def get_top_trend_countries(pk, countries):
    trends_list = []
    # for country in countries:
    #     top_trends = Trends.objects.filter(keyword_id=pk, country=country).order_by('-notrend')[:5]
    #     for trend in top_trends:
    #         if trend.trend not in trends_list:
    #             trends_list.append(trend.trend)
    top_trends = Trends.objects.filter(keyword_id=pk).order_by('-notrend')[:70]
    for trend in top_trends:
        if trend.trend not in trends_list:
            trends_list.append(trend.trend)
    return trends_list


def get_tweet_with_filter_key(pk, filter_key):
    tweet_list = Tweet.objects.filter(keyword=pk, text__icontains=filter_key)
    return tweet_list


def get_keyword_by_id(pk):
    keyword = Keyword.objects.get(pk=pk)
    return keyword


def analyse_wordcloud(tweet_list, request):
    text = " ".join([tweet.text for tweet in tweet_list])
    sws = stopwords.words('english')
    # sws.update(["https", "amp", "RT", "co", "I"])

    wordcloud = WordCloud(font_path='NanumMyeongjo.ttf', stopwords=sws, background_color="white", width=1200,
                          height=700, collocations=False).generate(text)
    wordcloud.to_file(f"event_detection/static/event_detection/{request.user.username}.png")

    return f'event_detection/{request.user.username}.png'


def ngrams_visualization(counter, ngrams):
    count_list = counter.most_common()[:20]
    # count_list.reverse()

    fig = go.Figure()
    bar = go.Bar(x=[' '.join(value[0]) for value in count_list], y=[value[1] for value in count_list])
    fig.add_trace(bar)
    fig.update_layout(
        xaxis=dict(
            title=f'{ngrams}-grams',
        ),
        yaxis=dict(
            title='Count'
        ),
        title=f'{ngrams}-grams Distribution'
    )

    plot_div = plot(fig,
                    output_type='div',
                    include_plotlyjs=False,
                    show_link=False,
                    link_text="")

    return plot_div


def extract_entity(text, nlp):
    add = ['amp', '.', "'", 'via', 'cc', 'RT', 'dont', 'cant', 'doesnt', '&amp', 'must', 'need', 'get', 'youre', 'gon',
           'im', 'na']
    text = " ".join([word for word in text.split() if not word.lower() in add])

    doc = nlp(text.strip())

    name_entities = set([ent for ent in doc.ents])
    entities = []
    for ent in name_entities:
        entities.append(str(ent))

    return entities


def extract_ngrams(tweet, nlp):
    all_stopwords = nlp.Defaults.stop_words
    trend_list = []
    add = ['amp', '.', 'via', 'cc', 'RT', 'dont', 'cant', 'doesnt', '&amp', 'must', 'need', 'get', 'youre', 'gon',
           'im', 'na', 'the', 'i', 'but', 'this', 'that', 'vs', 'and', 'it', 'you', 'vs', 'we', 'got', 'want', 'they',
           'then', 'can', 'he', 'went', 'if', 'its']
    doc = nlp(tweet)
    text_tokens = [token.text.strip() for token in doc]

    tokens = [word.strip() for word in text_tokens if
              (not word in all_stopwords) and (not word.lower() in add) and (len(word) > 3)]
    # one_gram = ngrams(tokens, 1)
    two_gram = ngrams(tokens, 2)
    thr_gram = ngrams(tokens, 3)
    # fou_gram = ngrams(tokens, 4)
    # fif_gram = ngrams(tokens, 5)
    # for value in one_gram:
    #     trend_list.append(" ".join(value))
    for value in two_gram:
        trend_list.append(" ".join(value))
    for value in thr_gram:
        trend_list.append(" ".join(value))
    # for value in one_gram:
    #     trend_list.append(" ".join(value))

    return trend_list


def analyse_ngrams(tweet_list):
    one_gram_counter, two_gram_counter, thr_gram_counter = extract_ngrams(tweet_list)

    one_gram_plot_div = ngrams_visualization(one_gram_counter, 1)
    two_gram_plot_div = ngrams_visualization(two_gram_counter, 2)
    thr_gram_plot_div = ngrams_visualization(thr_gram_counter, 3)

    return one_gram_plot_div, two_gram_plot_div, thr_gram_plot_div


def extract_and_save_knowledge_graph_all_tweets(tweet_list):
    pass


# def get_db_knowledge_graph(pk):
#     pk = int(pk)
#     db_kg = DB_knowledge.objects.filter(keyword=pk)
#     return db_kg


def extract_knowledge_graph(tweet_list):
    exist_ids = set()
    new_tweet_list = []
    for tweet in tweet_list:
        tweet_id = tweet.tweet_id
        retweeted_id = tweet.retweeted_id

        if retweeted_id == 0 or retweeted_id == 1:  # 0 means not retweet, 1 means retweet
            if tweet_id not in exist_ids:
                exist_ids.add(tweet_id)
                new_tweet_list.append(tweet)
        elif retweeted_id not in exist_ids:
            exist_ids.add(retweeted_id)
            new_tweet_list.append(tweet)

    knowledge_graph = []
    # c = 0

    for tweet in new_tweet_list:
        knowledge_list = tweet.knowledge.all()
        if knowledge_list is not None and len(knowledge_list) > 0:
            triple_list = []
            for knowledge in knowledge_list:
                triple_list.append((knowledge.k_subject,
                                    knowledge.k_predicate,
                                    knowledge.k_object,
                                    knowledge.subject_type,
                                    knowledge.object_type,
                                    ))
                break

            # knowledge_graph_dict[tweet.tweet_id] = (
            #     tweet.text, triple_list, tweet.created_at.strftime("%Y/%m/%d, %H:%M:%S"))
            knowledge_graph.append({
                'id': tweet.tweet_id,
                'tweet': tweet.text,
                'triple': triple_list,
                'created_at': tweet.created_at.strftime("%Y/%m/%d, %H:%M:%S"),
                'is_new_knowledge': knowledge_list[0].is_new_knowledge})
    new_knowledge_graph = []
    key_counts = Counter(' '.join(d['triple'][0]) for d in knowledge_graph)
    for d in knowledge_graph:
        d['count'] = key_counts[' '.join(d['triple'][0])]
        new_knowledge_graph.append(d)
    return new_knowledge_graph


def suggest_keyword_from_dbpedia(pk):
    keyword = get_keyword_by_id(pk)
    d = dbpedia_query.link_entity(keyword.keyword, None, limit=5)
    related_keywords = []
    for entity, name in d.items():
        if name not in related_keywords:
            related_keywords.append(name)
    return related_keywords


def get_suggest_keyword_from_dbpedia(pk):
    pk = int(pk)
    suggest_keywords = []
    raw_suggest_keywords = TopicsDB.objects.raw(
        "SELECT 1 as id, related_topic FROM public.event_detection_topicsdb WHERE keyword_id = '%s'", [pk])
    for topic in raw_suggest_keywords:
        suggest_keywords.append(str(topic))
    return suggest_keywords


def get_keyword_dbpedia_graph(entity):
    d = dbpedia_query.link_entity(entity, None, limit=5)

    for entity, name in d.items():
        # related_entity_graph = dbpedia_query.entity_relate_object_two_level(entity)
        related_entity_graph = dbpedia_query.entity_relate_object(entity)

        return related_entity_graph
