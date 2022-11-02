from django import forms
from .models import Keyword, TwitterToken, Countries
from django.utils import timezone
from django.contrib.auth.models import User


class KeywordSearchForm(forms.ModelForm):
    countries_selection = forms.ModelMultipleChoiceField(queryset=Countries.objects.none())
    class Meta:
        model = Keyword
        # fields = ('keyword', 'end_date', 'token_selection', 'countries_selection')
        fields = ('keyword', 'end_date', 'countries_selection')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(KeywordSearchForm, self).__init__(*args, **kwargs)

        # user_tokens = self.user.tokens.all()
        # admin_user = User.objects.get(username='admin')
        # admin_tokens = admin_user.tokens.all()
        # tokens = user_tokens | admin_tokens
        # # print(tokens)
        countries = Countries.objects.all()
        # print(countries)
        self.fields['countries_selection'] = forms.ModelMultipleChoiceField(queryset=countries)
        # self.fields['token_selection'] = forms.ModelChoiceField(queryset=tokens,
        #                                                         widget=forms.Select(attrs={"onChange": 'checkToken()'}))

class NewsSearchForm(forms.ModelForm):
    token_selection = forms.ModelChoiceField(queryset=TwitterToken.objects.none(),
                                             widget=forms.Select(attrs={"onChange": 'checkToken()'}))
    class Meta:
        model = Keyword
        fields = ('keyword', 'end_date', 'token_selection')
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(NewsSearchForm, self).__init__(*args, **kwargs)
        user_tokens = self.user.tokens.all()
        admin_user = User.objects.get(username='admin')
        admin_tokens = admin_user.tokens.all()
        tokens = user_tokens | admin_tokens
        self.fields['token_selection'] = forms.ModelChoiceField(queryset=tokens, widget=forms.Select(attrs={"onChange": 'checkToken()'}))

class TokenAddForm(forms.ModelForm):
    class Meta:
        model = TwitterToken
        fields = ('consumer_key', 'consumer_secret', 'access_token', 'access_token_secret')


class SelectTimeRangeForm(forms.Form):
    start_date = forms.DateTimeField(input_formats=['%d/%m/%Y %H:%M'])
    end_date = forms.DateTimeField(input_formats=['%d/%m/%Y %H:%M'])


class KeywordAnalysisForm(forms.ModelForm):
    CHOICES = [('Option 1', 'Minute'), ('Option 2', 'Hour'), ('Option 3', 'Day'), ('Option 4', 'Week'),
               ('Option 5', 'Month')]
    time_option = forms.ChoiceField(label='Show by time frequency', choices=CHOICES)

    class Meta:
        model = Keyword
        fields = ('keyword', )