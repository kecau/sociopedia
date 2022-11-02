from django.contrib import admin

# Register your models here.
from .models import TwitterToken, Keyword, Tweet, Knowledge, TopicsDB, Trends, Temporal_knowledge, Events, Unique_knowledge

admin.site.register(TwitterToken)
admin.site.register(Keyword)
admin.site.register(Tweet)
admin.site.register(Knowledge)
admin.site.register(TopicsDB)
admin.site.register(Trends)
admin.site.register(Temporal_knowledge)
admin.site.register(Events)
admin.site.register(Unique_knowledge)
