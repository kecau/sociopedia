from django.shortcuts import render, redirect
from .forms import KeywordSearchForm, KeywordAnalysisForm, SelectTimeRangeForm, TokenAddForm, NewsSearchForm
from .utils import crawl_data
from django.http import JsonResponse
from .models import Keyword, Tweet, TwitterToken, TopicsDB, Trends, Events, Temporal_knowledge, Knowledge, \
    Unique_knowledge
from django.views.decorators.csrf import csrf_exempt
# from event_detection.models import Events, Temporal_knowledge
from tqdm import tqdm
import spacy
from event_detection.utils import datetime_utils

nlp = spacy.load("en_core_web_sm")
# from django.db.models import Count
import json
# from django.core.serializers.json import DjangoJSONEncoder
# from plotly.offline import plot
# import plotly.graph_objs as go
# import collections
# from collections import Counter

from datetime import datetime, timedelta
from datetimerange import DateTimeRange
import datetime as dt
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
# from wordcloud import WordCloud, STOPWORDS
# import threading
from django.core import serializers
from django.utils import timezone
# from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .utils import utils
from event_detection.utils import dbpedia_query, event_detect, knowledge_graph_extract


# import base64
# import ast


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('/')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})


@login_required
def search(request):
    if request.method == 'POST':
        form = KeywordSearchForm(request.POST, user=request.user)

        if form.is_valid():
            post = form.save(commit=False)
            countries_obj = form.cleaned_data['countries_selection']
            countries = []
            for country in countries_obj:
                countries.append(country.country_name)
            # print(countries)
            keyword_obj_list = []
            for keyword in post.keyword.strip().split(','):
                keyword_obj = Keyword.objects.create(user=request.user, keyword=keyword.strip(),
                                                     search_date=timezone.now(), end_date=post.end_date,
                                                     countries=countries, resource=0)
                # search db
                related_topics = utils.suggest_keyword_from_dbpedia(keyword_obj.id)
                if related_topics != None:
                    for topic in related_topics:
                        TopicsDB.objects.create(keyword=keyword_obj, related_topic=topic)
                keyword_obj_list.append(keyword_obj)
            # used_token = form.cleaned_data['token_selection']
            # countries = form.cleaned_data['countries_selection']
            stream = crawl_data.stream_search(keyword_obj_list, countries_obj, nlp)

            is_error = None
            if stream is False:
                is_error = True

            return render(request, 'keyword_search.html',
                          {'title': 'search', 'form': form, 'keyword_obj_list': keyword_obj_list, 'is_error': is_error})

    form = KeywordSearchForm(user=request.user)
    end_date = timezone.now() + timedelta(30 * 5)
    form['end_date'].initial = end_date

    min_date = timezone.now().strftime("%Y/%m/%d")
    max_date = end_date.strftime("%Y/%m/%d")

    return render(request, 'keyword_search.html',
                  {'title': 'search', 'form': form, 'min_date': min_date, 'max_date': max_date})


@login_required
def search_news(request):
    if request.method == 'POST':
        form = NewsSearchForm(request.POST, user=request.user)
        if form.is_valid():
            post = form.save(commit=False)
            countries = ["United States", "China", "Japan"]
            keyword_obj_list = []
            for keyword in post.keyword.strip().split(','):
                keyword_obj = Keyword.objects.create(user=request.user, keyword=keyword.strip(),
                                                     search_date=timezone.now(), end_date=post.end_date,
                                                     countries=countries, resource=1)
                # search db
                related_topics = utils.suggest_keyword_from_dbpedia(keyword_obj.id)
                print("related_topics: ", related_topics)

                if related_topics != None:
                    for topic in related_topics:
                        TopicsDB.objects.create(keyword=keyword_obj, related_topic=topic)
                keyword_obj_list.append(keyword_obj)
            used_token = form.cleaned_data['token_selection']
            stream = crawl_data.stream_news(keyword_obj_list, nlp, used_token)
            is_error = None
            if stream is False:
                is_error = True

            return render(request, 'keyword_search.html',
                          {'title': 'search', 'form': form, 'keyword_obj_list': keyword_obj_list, 'is_error': is_error})

    form = NewsSearchForm(user=request.user)
    end_date = timezone.now() + timedelta(30 * 5)
    form['end_date'].initial = end_date

    min_date = timezone.now().strftime("%Y/%m/%d")
    max_date = end_date.strftime("%Y/%m/%d")

    return render(request, 'search_news.html',
                  {'title': 'search_news', 'form': form, 'min_date': min_date, 'max_date': max_date})


@csrf_exempt
def load_keyword_ajax(request):
    if request.is_ajax and request.method == "POST":
        keyword_id = request.POST.get('id', None)
        countries = Keyword.objects.filter(id=keyword_id)[0].countries
        top_trends = utils.get_top_trend_countries(keyword_id, countries)
        # top_trends = utils.get_top_trend(keyword_id)
        dbpedia_keywords = utils.get_suggest_keyword_from_dbpedia(keyword_id)
        # keywords.extend(dbpedia_keywords)
        return JsonResponse({'top_trends': top_trends, 'dbpedia_keywords': dbpedia_keywords, 'countries': countries},
                            status=200)

    return JsonResponse({"error": ""}, status=400)


@csrf_exempt
def detect_event_ajax(request):
    if request.is_ajax and request.method == "POST":
        keyword_id = request.POST.get('id', None)  # id keyword search
        # start_date = request.POST.get('start_date', None)
        # end_date = request.POST.get('end_date', None)
        trend = request.POST.get('trend', None)  # selected trend
        keyword_obj = Keyword.objects.filter(id=keyword_id)[0]
        knowledge_graph_list = []
        db_knowledge_graph_list = []
        events = []
        raw_events = Events.objects.filter(keyword_id=keyword_id, trend=trend).order_by('begin_time')
        for event in raw_events:
            events.append((str(event)[0:16], str(event)[18:34]))
        print("event ", len(events))
        check = []
        trend_obj = Trends.objects.filter(keyword_id=keyword_id, trend=trend)[0]
        print("trend_obj", trend_obj)
        x_data = trend_obj.x_data_date_event[0]
        # print("no of events: ", len(events))
        temporal_knowledge = Temporal_knowledge.objects.filter(keyword_id=keyword_id)
        for event in tqdm(events):
            event_st = datetime.strptime(event[0], "%Y-%m-%d %H:%M")
            event_en = datetime.strptime(event[1], "%Y-%m-%d %H:%M")
            knowledge_list = []
            for knowledge in temporal_knowledge:
                score = sum(knowledge.occurrence[x_data.index(event[0]): x_data.index(event[1])])
                if (score != 0) and (
                set(trend.lower().split(" ")).issubset(set(knowledge.tweet.text.lower().split(" ")))):
                    timeline = knowledge.timeline
                    countries_knowledge = []
                    label_knowledge = []
                    group_tweets_id = knowledge.group_tweets_id
                    for t in timeline:
                        ts = datetime.strptime(t[0], "%Y-%m-%d %H:%M")
                        te = datetime.strptime(t[1], "%Y-%m-%d %H:%M")
                        tmp_countries = []
                        tmp_label = []
                        for tweet_id in group_tweets_id:
                            public_time = datetime.strptime(
                                Tweet.objects.filter(id=tweet_id)[0].created_at.strftime("%Y-%m-%d %H:%M"),
                                "%Y-%m-%d %H:%M")
                            if (public_time >= ts) and (public_time <= te):
                                tmp_countries.append(Tweet.objects.filter(id=tweet_id)[0].country)
                                tmp_label.append(Tweet.objects.filter(id=tweet_id)[0].label)

                        countries_knowledge.append(tmp_countries)
                        label_knowledge.append(tmp_label)

                    knowledge_list.append({
                        'id': knowledge.tweet_id,
                        'tweet': knowledge.tweet.text,
                        'created_at': knowledge.tweet.created_at,
                        'subject': knowledge.k_subject,
                        'predicate': knowledge.k_predicate,
                        'object': knowledge.k_object,
                        'time_start': knowledge.temporal_start,
                        'time_end': knowledge.temporal_end,
                        'mentions': score,
                        'is_new_knowledge': knowledge.is_new_knowledge,
                        'country': countries_knowledge,
                        'timeline': knowledge.timeline,
                        'label': label_knowledge,
                        'occurrence': knowledge.occurrence,
                        'diffuse_degree': knowledge.diffuse_degree
                    })

            if knowledge_list == []:
                check.append(event)
            else:
                # db_knowledge_graph = knowledge_graph_extract.get_DBpedia_knowledge_graph(knowledge_list)
                # for triple in db_knowledge_graph[1]:
                #     knowledge_list.append(triple)
                knowledge_graph_list.append(knowledge_list)
                # db_knowledge_graph_list.append(db_knowledge_graph[0])


            # else:
            #     check.append(event)
        for i in check:
            events.remove(i)
        sentiment_data = {}
        sentiment_plot = []
        event_plot = []
        countries = keyword_obj.countries

        if len(list(trend_obj.x_data_date_event)) == 0:
            tweets_list = utils.get_tweet_in_time_range_countries(keyword_obj.id, "", "", countries, "")
            time = []
            for tweets in tweets_list:
                for tweet in tweets:
                    time.append(tweet.created_at)

            start_date = datetime_utils.correct_time(min(time).strftime("%Y-%m-%d %H"))
            end_date = datetime_utils.correct_time(max(time).strftime("%Y-%m-%d %H"))
            print("check ", start_date, end_date)
            x_data_date_event, y_proportion_group = event_detect.get_tweet_distribution_countries_event(tweets_list,
                                                                                                        trend,
                                                                                                        countries)

            event_plot = utils.plot_proportion_countries(x_data_date_event, y_proportion_group, countries,
                                                         events, trend)
            pos_tweets = utils.get_tweet_sentiment_countries(keyword_obj, countries, "positive", start_date, end_date)
            neg_tweets = utils.get_tweet_sentiment_countries(keyword_obj, countries, "negative", start_date, end_date)
            neu_tweets = utils.get_tweet_sentiment_countries(keyword_obj, countries, "neutral", start_date, end_date)
            # print(len(pos_tweets), len(neg_tweets), len(neu_tweets))
            x_pos_sentiment, y_pos_sentiment = event_detect.tweets_distribution_countries(start_date, end_date,
                                                                                          pos_tweets, trend)
            x_neg_sentiment, y_neg_sentiment = event_detect.tweets_distribution_countries(start_date, end_date,
                                                                                          neg_tweets, trend)
            x_neu_sentiment, y_neu_sentiment = event_detect.tweets_distribution_countries(start_date, end_date,
                                                                                          neu_tweets, trend)

            sentiment_data['x_data_date'] = x_data_date_event
            sentiment_data['positive'] = y_pos_sentiment
            sentiment_data['negative'] = y_neg_sentiment
            sentiment_data['neutral'] = y_neu_sentiment
            sentiment_plot = utils.plot_sentiment_countries(countries, sentiment_data, trend, events)


        else:
            event_plot = utils.plot_proportion_countries(trend_obj.x_data_date_event, trend_obj.y_proportion, countries,
                                                         events, trend)
            sentiment_data['x_data_date'] = trend_obj.x_data_date_event
            sentiment_data['positive'] = trend_obj.y_pos_sentiment
            sentiment_data['negative'] = trend_obj.y_neg_sentiment
            sentiment_data['neutral'] = trend_obj.y_neu_sentiment
            sentiment_plot = utils.plot_sentiment_countries(countries, sentiment_data, trend, events)
        print("done plot")
        # y_data_list = trend_obj.y_data_event
        # sum_z = 0
        # for y_data in y_data_list:
        #     sum_z += sum(y_data)
        # print("no tweets: ", sum_z)

        return JsonResponse(
            {'event_plot': event_plot, 'sentiment_plot': sentiment_plot, 'knowledgegraph': knowledge_graph_list,
             'events': events,
             'db_knowledge_graph': db_knowledge_graph_list, 'filter_key': trend}, status=200)

    return JsonResponse({"error": ""}, status=400)


@login_required
def keywords_management(request):
    keywords = request.user.keywords.all()
    current_time = timezone.now()
    new_keyword = []
    blacklist = [451, 447]
    for keyword in keywords:
        if keyword.end_date < current_time:
            keyword.is_streaming = False
        # else:
        #     keyword.is_streaming = True
        if keyword.id not in blacklist:
            # if (keyword.id > 373) and (keyword.id < 431):
            keyword.n_tweets = keyword.tweets.count()
            new_keyword.append(keyword)

    return render(request, 'keywords_management.html', {'title': 'keywords_management', 'keywords': new_keyword})


def api_document(request):
    return render(request, 'api_document.html', {'title': 'api_document'})


@csrf_exempt
def delete_keyword(request):
    if request.method == "GET":
        keyword_id = request.GET.get('keyword_id', None)
        print("check ajax")
        # Tweet.objects.filter(keyword_id=keyword_id).delete()
        # Trends.objects.filter(keyword_id=keyword_id).delete()
        # Temporal_knowledge.objects.filter(keyword_id=keyword_id).delete()
        # Knowledge.objects.filter(keyword_id=keyword_id).delete()
        # Unique_knowledge.objects.filter(keyword_id=keyword_id).delete()
        # TopicsDB.objects.filter(keyword_id=keyword_id).delete()
        Keyword.objects.filter(id=keyword_id).delete()
        return JsonResponse({"id": keyword_id}, status=200)

    return JsonResponse({"error": "not ajax request"}, status=400)


@csrf_exempt
def stop_streaming(request):
    if request.method == "GET":
        keyword_id = request.GET.get('keyword_id', None)
        Keyword.objects.filter(id=keyword_id).update(is_forced_stop=True, is_streaming=False)
        return JsonResponse({"id": keyword_id}, status=200)

    return JsonResponse({"error": "not ajax request"}, status=400)


@login_required
def view_analysis(request, pk):
    keyword_id = pk
    top_trends = utils.get_top_trend(keyword_id)
    dbpedia_keywords = utils.get_suggest_keyword_from_dbpedia(keyword_id)
    return render(request, 'view_analysis.html', {'title': 'keywords_management',
                                                  'keyword_id': pk,
                                                  'top_trends': top_trends,
                                                  'dbpedia_keywords': dbpedia_keywords}
                  )


@csrf_exempt
def load_tweet_dist(request):
    if request.is_ajax and request.method == "POST":
        keyword_id = request.POST.get('id', None)
        # tweet_list = Tweet.objects.filter(keyword=keyword_id)
        # plot_div = utils.plot_distribution(tweet_list, time_option=time_option)
        keyword_obj = Keyword.objects.filter(id=keyword_id)[0]
        x_data_date_group = keyword_obj.x_data_date
        y_data_group = keyword_obj.y_data
        countries = keyword_obj.countries
        # print(countries)
        if keyword_obj.x_data_date is None or keyword_obj.x_data_date == {}:
            tweets_list = utils.get_tweet_in_time_range_countries(keyword_obj.id, "", "", countries, "")
            time = []
            for tweets in tweets_list:
                for tweet in tweets:
                    time.append(tweet.created_at)
            start_date = datetime_utils.correct_time(min(time).strftime("%Y-%m-%d %H"))
            end_date = datetime_utils.correct_time(max(time).strftime("%Y-%m-%d %H"))
            print("check dis ", start_date, end_date)
            x_data_date_group, y_data_group = event_detect.tweets_distribution_countries(start_date, end_date,
                                                                                         tweets_list, trend="")
            plot_div = utils.plot_distribution_countries(x_data_date_group, y_data_group, countries)
        else:
            plot_div = utils.plot_distribution_countries(x_data_date_group, y_data_group, countries)
        return JsonResponse({'tweets_div': plot_div}, status=200)

    return JsonResponse({"error": ""}, status=400)


@csrf_exempt
def load_timeline(request):
    if request.is_ajax and request.method == "POST":
        knowledgegraph = json.loads(request.POST['knowledgegraph'])
        plot_div = utils.plot_timeline(knowledgegraph)
        # plot_div = []
        return JsonResponse({'plot_timeline_visual': plot_div}, status=200)

    return JsonResponse({"error": ""}, status=400)


@csrf_exempt
def event_timeline(request):
    if request.is_ajax and request.method == "POST":
        knowledgegraphs = json.loads(request.POST['knowledgegraphs'])
        events = json.loads(request.POST['events'])
        plot_div = utils.plot_event_timeline(knowledgegraphs, events)
        plot_div_chart = utils.plot_event_timeline_chart(knowledgegraphs, events)
        return JsonResponse({'plot_event_timeline': plot_div,
                             'plot_event_timeline_chart': plot_div_chart}, status=200)

    return JsonResponse({"error": ""}, status=400)


@csrf_exempt
def load_timeline_knowledge(request):
    if request.is_ajax and request.method == "POST":
        knowledgegraph = json.loads(request.POST['knowledgegraph'])
        events = json.loads(request.POST['event'])
        keyword_id = json.loads(request.POST['keyword_id'])
        print("check load_timeline_knowledge")

        keyword_obj = Keyword.objects.filter(id=keyword_id)[0]
        time = []
        tweets_list = Tweet.objects.filter(keyword_id=keyword_obj)
        for tweet in tweets_list:
            time.append(tweet.created_at)

        start_date = datetime_utils.correct_time(min(time).strftime("%Y-%m-%d %H"))
        end_date = datetime_utils.correct_time(max(time).strftime("%Y-%m-%d %H"))
        print("start date ", start_date, end_date)
        plot_div = utils.plot_timeline_knowledge(knowledgegraph, events, start_date, end_date)
        return JsonResponse({'plot_timeline_knowledge': plot_div}, status=200)

    return JsonResponse({"error": ""}, status=400)


@csrf_exempt
def load_characteristics(request):
    if request.is_ajax and request.method == "POST":
        knowledgegraph = json.loads(request.POST['knowledgegraph'])
        event = json.loads(request.POST['event'])
        keyword_id = json.loads(request.POST['keyword_id'])
        print("check load_characteristics")
        keyword_obj = Keyword.objects.filter(id=keyword_id)[0]
        # start_date = keyword_obj.search_date.strftime("%Y-%m-%d %H:%M")
        # end_date = keyword_obj.end_date.strftime("%Y-%m-%d %H:%M")
        time = []
        tweets_list = Tweet.objects.filter(keyword_id=keyword_obj)
        for tweet in tweets_list:
            time.append(tweet.created_at)

        start_date = datetime_utils.correct_time(min(time).strftime("%Y-%m-%d %H"))
        end_date = datetime_utils.correct_time(max(time).strftime("%Y-%m-%d %H"))
        print("start date ", start_date, end_date)
        plot_div_occurrence_time, plot_div_diffuse_degree_time = utils.plot_characteristics_time(knowledgegraph, event,
                                                                                                 start_date, end_date)
        print("done plot_characteristics_time")

        time_range = DateTimeRange(start_date, end_date)
        time = []
        group_len = []
        for value in time_range.range(dt.timedelta(hours=1)):
            time.append(value.strftime("%Y-%m-%d %H:%M"))
        # for value in time_range.range(dt.timedelta(minutes=1)):
        #     time.append(value.strftime("%Y-%m-%d %H:%M"))
        for index in range(len(event)):
            ts = time.index(event[index][0])
            te = time.index(event[index][1])
            # print(ts, te)
            for knowledge in knowledgegraph[index]:
                knowledge['diffuse_degree'] = knowledge['diffuse_degree'][ts:te]
                knowledge['occurrence'] = knowledge['occurrence'][ts:te]
                group_len.append(len(knowledge['diffuse_degree']))
        max_len = max(group_len)
        print("max_len:", max_len)
        for index in range(len(event)):
            for knowledge in knowledgegraph[index]:
                if len(knowledge['diffuse_degree']) < max_len:
                    for i in range(max_len - len(knowledge['diffuse_degree'])):
                        knowledge['diffuse_degree'].append(0)
                        knowledge['occurrence'].append(0)
        plot_div_occurrence_frequency, plot_div_diffuse_degree_frequency, plot_div_occurrence_psd, plot_div_diffuse_degree_psd = utils.plot_characteristics(
            knowledgegraph, max_len)
        print("done plot_characteristics")

        return JsonResponse({'plot_div_occurrence_time': plot_div_occurrence_time,
                             'plot_div_diffuse_degree_time': plot_div_diffuse_degree_time,
                             'plot_div_occurrence_frequency': plot_div_occurrence_frequency,
                             'plot_div_diffuse_degree_frequency': plot_div_diffuse_degree_frequency,
                             'plot_div_occurrence_psd': plot_div_occurrence_psd,
                             'plot_div_diffuse_degree_psd': plot_div_diffuse_degree_psd}, status=200)

    return JsonResponse({"error": ""}, status=400)


@csrf_exempt
def filter_tweets_intime(request):
    if request.is_ajax and request.method == "POST":
        keyword_id = request.POST.get('id', None)
        start_date = request.POST.get('start_date', None)
        end_date = request.POST.get('end_date', None)
        page_n = request.POST.get('page_n', None)
        tweet_list = utils.get_tweet_in_time_range(keyword_id, start_date, end_date, "")

        page = int(page_n)
        tweets, tweet_index, page_range = utils.paging_tweets(tweet_list, page)

        page_settings = {}
        page_settings['has_other_pages'] = tweets.has_other_pages()
        page_settings['has_previous'] = tweets.has_previous()
        page_settings['number'] = tweets.number
        page_settings['has_next'] = tweets.has_next()
        if tweets.has_previous():
            page_settings['previous_page_number'] = tweets.previous_page_number()
        if tweets.has_next():
            page_settings['next_page_number'] = tweets.next_page_number()

        # for tweet in tweets:
        #     tweet.user_id = str(tweet.user_id)
        #     tweet.tweet_id = str(tweet.tweet_id)

        tweets = serializers.serialize('json', tweets)

        return JsonResponse(
            {"tweets": tweets, "tweet_index": tweet_index, "page_range": page_range,
             'page_settings': page_settings},
            status=200)

    return JsonResponse({"error": ""}, status=400)


@csrf_exempt
def link_entity_dbpedia(request):
    if request.is_ajax and request.method == "POST":
        entity = request.POST.get('entity', None)
        entity_type = request.POST.get('type', None)
        dbpedia_entity = dbpedia_query.link_entity(entity, entity_type, limit=10)
        return JsonResponse({'dbpedia_entity': dbpedia_entity}, status=200)

    return JsonResponse({"error": ""}, status=400)


@csrf_exempt
def question_answering_ajax(request):
    if request.is_ajax and request.method == "POST":
        question = request.POST.get('question', None)
        entities, relations = knowledge_graph_extract.extract_entity_question(question)

        return JsonResponse({'entities': entities, 'relations': relations}, status=200)

    return JsonResponse({"error": ""}, status=400)


@login_required
def token_management(request):
    if request.method == 'POST':
        form = TokenAddForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()

    form = TokenAddForm()

    user_tokens = request.user.tokens.all()
    # admin_user = User.objects.get(username='admin')
    # admin_tokens = admin_user.tokens.all()

    # for token in list(admin_tokens):
    #     token.consumer_key = token.consumer_key[:3] + "".join(["*" for i in range(len(token.consumer_key) - 3)])
    #     token.consumer_secret = token.consumer_secret[:3] + "".join(["*" for i in range(len(token.consumer_secret) - 3)])
    #     token.access_token = token.access_token[:3] + "".join(["*" for i in range(len(token.access_token) - 3)])
    #     token.access_token_secret = token.access_token_secret[:3] + "".join(["*" for i in range(len(token.access_token_secret) - 3)])

    tokens = user_tokens  # | admin_tokens
    # tokens = list(user_tokens)
    # tokens.extend(list(admin_tokens))

    return render(request, 'token_management.html', {'title': 'token_management', 'form': form, 'tokens': tokens})


def delete_token(request, pk):
    if request.method == 'POST':
        form = TokenAddForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()

    form = TokenAddForm()

    user_tokens = request.user.tokens.all()
    admin_user = User.objects.get(username='admin')

    delete_token = TwitterToken.objects.filter(id=pk).first()
    if request.user != admin_user and delete_token.user == admin_user:
        pass
    else:
        delete_token.delete()

    admin_tokens = admin_user.tokens.all()

    # for token in list(admin_tokens):
    #     token.consumer_key = token.consumer_key[:3] + "".join(["*" for i in range(len(token.consumer_key) - 3)])
    #     token.consumer_secret = token.consumer_secret[:3] + "".join(["*" for i in range(len(token.consumer_secret) - 3)])
    #     token.access_token = token.access_token[:3] + "".join(["*" for i in range(len(token.access_token) - 3)])
    #     token.access_token_secret = token.access_token_secret[:3] + "".join(["*" for i in range(len(token.access_token_secret) - 3)])

    tokens = user_tokens  # | admin_tokens
    # tokens = list(user_tokens)
    # tokens.extend(list(admin_tokens))

    return render(request, 'token_management.html', {'title': 'token_management', 'form': form, 'tokens': tokens})


@csrf_exempt
def token_streaming_count_check(request):
    if request.is_ajax and request.method == "POST":
        token_id = request.POST.get('token_id', None)
        token = TwitterToken.objects.filter(id=token_id).first()
        token_check = token.token_check

        return JsonResponse({'token_check': token_check}, status=200)

    return JsonResponse({"error": ""}, status=400)


def home(request):
    return render(request, 'home.html', {'title': 'home'})


def about(request):
    return render(request, 'about.html', {'title': 'about'})
