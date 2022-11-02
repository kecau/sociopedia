import datetime as dt
import requests
import xml.etree.ElementTree as ET
import html


def crawling_news(keyword):
    news_list = []
    # print(keyword)
    parameters = {'q': keyword}
    # response = requests.get('https://news.google.com/rss/search', params=parameters)
    response = requests.get('https://news.google.com/rss/search?', params=parameters)
    # response.encoding = response.apparent_encoding
    tmp = html.unescape(response)
    root = ET.fromstring(tmp.text)
    # print(type(root))
    for item in root.iter('item'):
        # if keyword.lower() in item[0].text.lower():
        title = item[0].text
        link = item[1].text
        date_published = str(item[3].text)[5:-4]
        date_published = str(dt.datetime.strptime(date_published, '%d %b %Y %H:%M:%S'))
        html_code = item[4].text.replace("&nbsp;", " ")
        # print(html_code)
        # html_code = ET.fromstring(html_code)
        # for i in html_code:
        #     if i[0].attrib != {}:
        #         print(i[0].attrib['href'], i[0].text)
        # break
        news_list.append({
            'title': title,
            'date_published': date_published,
            'link': link,
            'html_code': html_code
        })
    #     # break

    return news_list

def get_related_news(keyword, nlp):
    # nlp = spacy.load("en_core_web_sm", disable=['ner', 'parser'])
    doc = nlp(keyword)
    new_key = [token.lemma_ for token in doc]
    crawled_news = crawling_news(keyword)
    related_new = []
    for title in crawled_news:
        nlp_title = nlp(title['title'].lower())
        new_title = [token.lemma_ for token in nlp_title]
        if all(item in new_title for item in new_key):
            related_new.append(title)
    return related_new
import spacy
keyword = 'biden agrees putin'
nlp = spacy.load("en_core_web_sm", disable=['ner', 'parser'])
print(get_related_news(keyword, nlp))
# import spacy
# nlp = spacy.load("en_core_web_sm", disable=['ner','parser'])
# doc = nlp(keyword)
# new_key = [token.lemma_ for token in doc]
# crawled_news = crawling_news(keyword)
# new_news = []
# for title in crawled_news:
#     nlp_title = nlp(title['title'].lower())
#     new_title = [token.lemma_ for token in nlp_title]
#     print(" ".join(new_title))
#     if all(item in new_title for item in new_key):
#         new_news.append(title)
# for news in new_news:
#     print(news)

# biden%20agrees%20putin
