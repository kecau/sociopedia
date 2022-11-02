# from django.shortcuts import render, redirect
# from .forms import KeywordSearchForm, KeywordAnalysisForm, SelectTimeRangeForm
# from .utils import twitter_search
# from django.http import JsonResponse
from .models import Keyword, Tweet, Trends
# from django.views.decorators.csrf import csrf_exempt
# import json
# from django.core.serializers.json import DjangoJSONEncoder
# from plotly.offline import plot
# import plotly.graph_objs as go
# import collections
# from datetime import datetime, timedelta
# from django.contrib.auth.models import User
# from django.contrib.auth.decorators import login_required
# from django.contrib.auth import login, authenticate
# from django.contrib.auth.forms import UserCreationForm
# from wordcloud import WordCloud, STOPWORDS
# import threading
# from django.core import serializers
# from django.utils import timezone
# from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .utils import utils
from event_detection.utils import dbpedia_query, event_detect, knowledge_graph_extract
import base64
import ast

from rest_framework import viewsets, permissions
from event_detection.serializers import KeywordSerializer, TweetSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination


class KeywordList(APIView):
    permission_classes = (IsAuthenticated,) 

    def get(self, request):
        queryset = request.user.keywords.all()
        serializer = KeywordSerializer(queryset, many=True)
        return Response(serializer.data)

class PaginationHandlerMixin(object):
    @property
    def paginator(self):
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        else:
            pass
        return self._paginator
    def paginate_queryset(self, queryset):
        
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset,
                   self.request, view=self)
    def get_paginated_response(self, data):
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)

class BasicPagination(PageNumberPagination):
    page_size_query_param = 'limit'

class TweetList(APIView, PaginationHandlerMixin):
    permission_classes = (IsAuthenticated,)
    pagination_class = BasicPagination
    serializer_class = TweetSerializer

    def get(self, request):

        keyword_id = request.query_params.get('keyword_id')
        keyword = Keyword.objects.get(pk=keyword_id)
        tweets = keyword.tweets.all()
        
        page = self.paginate_queryset(tweets)
        if page is not None:
            serializer = self.get_paginated_response(self.serializer_class(page, many=True).data)
        else:
            serializer = self.serializer_class(tweets, many=True)

        return Response(serializer.data)

class TopicList(APIView):
    def get(self, request):
        # keywords = []

        keyword_id = request.query_params.get('keyword_id')
        top_trends = utils.get_top_trend(keyword_id)
        # tweet_list = utils.get_tweet_in_time_range(keyword_id, None, None)
        # one_gram_counter, two_gram_counter, thr_gram_counter = utils.extract_ngrams(tweet_list)
        #
        # keywords.extend([' '.join(value[0]) for value in one_gram_counter.most_common()[:20]])
        # keywords.extend([' '.join(value[0]) for value in two_gram_counter.most_common()[:20]])
        # keywords.extend([' '.join(value[0]) for value in thr_gram_counter.most_common()[:20]])
        #
        # # dbpedia_keywords = utils.suggest_keyword_from_dbpedia(keyword_id)
        return Response({'topics': top_trends})

class EventList(APIView):
    def get(self, request):
        keyword_id = request.query_params.get('keyword_id')
        topic = request.query_params.get('topic')
        print(keyword_id, topic)

        tweet_list = utils.get_tweet_in_time_range(keyword_id, None, None,"")
        time_option = 'hour'
        x_data_date, y_data_event, y_data, y_proportion = event_detect.get_tweet_distribution_event(tweet_list, topic, time_option)

        burst_list, variables = event_detect.detect_event(y_data_event, y_data)

        events = []
        bursts = burst_list[0]
        for index, burst in bursts.iterrows():
            start = burst['begin']
            end = burst['end']
            
            start_time = x_data_date[start] #.strftime("%Y-%m-%d %H:%M")
            end_time = x_data_date[end] #.strftime("%Y-%m-%d %H:%M")
            
            events.append((start_time, end_time))

        return Response({"events": events})

class EventKnowledgeList(APIView):
    def get(self, request):
        keyword_id = request.query_params.get('keyword_id')
        topic = request.query_params.get('topic')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        tweet_list = utils.get_tweet_in_time_range(keyword_id, start_date, end_date, "")
        knowledge_graph_dict = utils.extract_knowledge_graph(tweet_list)

        return Response({"event_knowledge": knowledge_graph_dict})

class LinkingKnowledge(APIView):
    def get(self, request):
        keyword_id = request.query_params.get('keyword_id')
        topic = request.query_params.get('topic')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        entity = request.query_params.get('entity')

        tweet_list = utils.get_tweet_in_time_range(keyword_id, start_date, end_date, "")
        knowledge_graph_dict = utils.extract_knowledge_graph(tweet_list)

        keyword_knowledge_graph = []
        for _, knowledge in knowledge_graph_dict.items():
            triple_list = knowledge[1]
            for triple in triple_list:
                if entity.lower() == triple[0].lower():
                    keyword_knowledge_graph.append([entity, triple[1], triple[2], 'extracted'])
                elif entity.lower() == triple[2].lower():
                    keyword_knowledge_graph.append([triple[0], triple[1], entity, 'extracted'])

        keyword_dbpedia_graph = utils.get_keyword_dbpedia_graph(entity)

        keyword_knowledge_graph.append([entity, 'same as', "dbo:" + entity, 'dbpedia'])
        
        if keyword_dbpedia_graph is not None:
            # keyword_knowledge_graph.extend(keyword_dbpedia_graph)
            for key, value in keyword_dbpedia_graph.items():
                keyword_knowledge_graph.append(["dbo:" + entity, key, value, 'dbpedia'])

        return Response({"linking_knowledge": keyword_knowledge_graph})
