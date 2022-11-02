import urllib
import json
from django.utils.safestring import mark_safe
from django import template
register = template.Library()

@register.filter
def index(indexable, i):
    return indexable[i]

@register.filter
def get_encoded_dict(data_dict):
    return urllib.parse.urlencode(data_dict)

@register.filter(is_safe=True)
def js(obj):
    return mark_safe(json.dumps(obj))