from django.urls import path, include
from . import views, views_api
from rest_framework import routers
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.authtoken.models import Token

# router = routers.DefaultRouter()
# router.register(r'keywords', views.KeywordViewSet)

urlpatterns = [
    path('signup', views.signup, name='signup'),

    path('search', views.search, name='search'),
    path('search_news', views.search_news, name='search_news'),
    path('keywords_management', views.keywords_management, name='keywords_management'),
    path('api_document', views.api_document, name='api_document'),
    path('token_management', views.token_management, name='token_management'),

    # path('word_cloud', views.word_cloud, name='word_cloud'),
    # path('knowledge_graph', views.knowledge_graph, name='knowledge_graph'),
    path('view_analysis/<int:pk>/', views.view_analysis, name='view_analysis'),
    # path('data_analysis/<int:pk>/<str:start_date>/<str:end_date>/', views.data_analysis, name='data_analysis'),
    # path('detect_event/<int:pk>/<str:start_date>/<str:end_date>/', views.detect_event, name='detect_event'),
    # path('knowledge_graph_linking/<str:entity>/<str:knowledge_graph>/', views.knowledge_graph_linking,
    #      name='knowledge_graph_linking'),
    path('delete_token/<int:pk>/', views.delete_token, name="delete_token"),
    path('ajax/keyword_search', views.load_tweet_dist, name='load_tweet_dist'),
    path('ajax/keyword', views.delete_keyword, name='delete_keyword'),
    path('ajax/stop_streaming', views.stop_streaming, name='stop_streaming'),
    path('ajax/filter_tweets_intime', views.filter_tweets_intime, name='filter_tweets_intime'),
    # path('ajax/analyse', views.analyse, name='analyse'),
    path('ajax/link_entity_dbpedia', views.link_entity_dbpedia, name='link_entity_dbpedia'),
    path('ajax/detect_event_ajax', views.detect_event_ajax, name='detect_event_ajax'),
    path('ajax/load_timeline', views.load_timeline, name='load_timeline'),
    path('ajax/event_timeline', views.event_timeline, name='event_timeline'),
    # path('ajax/load_timeline_new', views.load_timeline, name='load_timeline_new'),
    path('ajax/load_characteristics', views.load_characteristics, name='load_characteristics'),
    path('ajax/load_timeline_knowledge', views.load_timeline_knowledge, name='load_timeline_knowledge'),
    path('ajax/load_keyword_ajax', views.load_keyword_ajax, name='load_keyword_ajax'),
    path('ajax/question_answering_ajax', views.question_answering_ajax, name='question_answering_ajax'),
    path('ajax/token_streaming_count_check', views.token_streaming_count_check, name='token_streaming_count_check'),

    path('', views.home, name='home'),
    # path('home', views.home, name='home'),
    path('about', views.about, name='about'),

    ### API
    # path('sociopedia/', include(router.urls)),
    # path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('keywords/', views_api.KeywordList.as_view(), name='keyword_list'),
    path('tweet_list/', views_api.TweetList.as_view(), name='tweet_list'),
    path('topic_list/', views_api.TopicList.as_view(), name='topic_list'),
    path('event_list/', views_api.EventList.as_view(), name='event_list'),
    path('event_knowledge_list/', views_api.EventKnowledgeList.as_view(), name='event_knowledge_list'),
    path('linking_knowledge/', views_api.LinkingKnowledge.as_view(), name='linking_knowledge'),
]