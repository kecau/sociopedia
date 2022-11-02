import re
import preprocessor as p
# from NewsSentiment import TargetSentimentClassifier
# tsc = TargetSentimentClassifier()

def remove_emoji(text):
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002500-\U00002BEF"  # chinese char
                               u"\U00002702-\U000027B0"
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               u"\U0001f926-\U0001f937"
                               u"\U00010000-\U0010ffff"
                               u"\u2640-\u2642"
                               u"\u2600-\u2B55"
                               u"\u200d"
                               u"\u23cf"
                               u"\u23e9"
                               u"\u231a"
                               u"\ufe0f"  # dingbats
                               u"\u3030"
                               "‘"
                               "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def remove_url(text):
    url_pattern = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    return url_pattern.sub(r'', text)

def remove_email(text):
    email_pattern = re.compile(r'[\w\.-]+@[\w\.-]+')
    return email_pattern.sub(r'', text)

def remove_mention(text):
    mention_pattern = re.compile(r'@+\w+')
    return mention_pattern.sub(r'', text)

def remove_number(text):
    number_pattern = re.compile(r'[0-9]+')
    return number_pattern.sub(r'', text)

def remove_hashtag(text):
    entity_prefixes = ['#','|']
    words = []
    for word in text.split():
        word = word.strip()
        if word:
            if word[0] not in entity_prefixes:
                words.append(word)
    return ' '.join(words)

def remove_stopwords(text):
    tokens = text.split()
    pass

def pre_process(text):
    text = text.replace('\n','.')
    text = text.replace('!','.')
    text = text.replace('?','.')
    text = remove_url(text)
    text = remove_hashtag(text)
    # text = remove_email(text)
    text = remove_mention(text)
    # text = remove_number(text)
    # text = remove_emoji(text)
    add = ['amp', ' ', 'via', 'cc', 'RT', 'dont', 'cant', 'doesnt', '&amp', 'must', 'need', 'get', 'youre', 'gon', 'im',
           'na']
    characters = '!?,/<>();:"\$%^&*-_=+|#'
    for char in characters:
        text = text.replace(char, '')
    text = " ".join([word for word in text.split() if not word.lower() in add])
    tmp = p.clean(text)
    return ' '.join(tmp.split())


def get_ner(sentence, nlp):
    doc = nlp(sentence)
    return doc.ents


def score_sentiment(keyword, sentences, nlp):
    outputs = []
    for sentence in sentences:
        mention_text = re.search(keyword.lower(), sentence.lower())
        if mention_text != None:
            text_left = sentence[0:mention_text.span()[0]]  # NOTE: must add a space before text mentioned
            text_mention = "korea"
            text_right = sentence[mention_text.span()[1]:len(sentence)]  # NOTE: must add a space after text mentioned
            sent = tsc.infer_from_text(text_left, text_mention, text_right)
            output = {
                "label": sent[0]['class_label'],
                "score": sent[0]['class_prob'],
            }
            outputs.append(output)
        else:
            ents = get_ner(sentence, nlp)
            if ents:
                text_left = sentence[0:ents[0].start_char] + " "  # NOTE: must add a space before text mentioned
                text_mention = ents[0].text
                text_right = " " + sentence[
                                   ents[0].end_char:len(sentence)]  # NOTE: must add a space after text mentioned

                sent = tsc.infer_from_text(text_left, text_mention, text_right)
                output = {
                    "label": sent[0]['class_label'],
                    "score": sent[0]['class_prob'],
                }

                outputs.append(output)
            else:
                continue

    return outputs


def get_label(scores):
    sum_positive = 0
    sum_negative = 0
    sum_neutral = 0
    result = {}
    for score in scores:
        if score["label"] == 'positive':
            sum_positive += 1
        if score["label"] == 'neutral':
            sum_neutral += 1
        if score["label"] == 'negative':
            sum_negative += 1
    max_value = max(sum_positive, sum_negative, sum_neutral)
    if sum_positive == max_value:
        result["label"] = "positive"
        result["score"] = 0
    if sum_negative == max_value:
        result["label"] = "negative"
        result["score"] = 0
    if sum_neutral == max_value:
        result["label"] = "neutral"
        result["score"] = 0
    return result