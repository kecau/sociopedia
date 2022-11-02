# import spacy

# nlp = spacy.load("en_core_web_sm")  # en_core_web_sm
from event_detection.utils import dbpedia_query, text_utils, utils, event_detect
from datetimerange import DateTimeRange
import datetime
from event_detection.models import Unique_knowledge, Temporal_knowledge, Knowledge, Tweet
from collections import Counter
from django.utils import timezone
from tqdm import tqdm
import tweepy
from event_detection.utils import datetime_utils

# Enter Twitter API Keys
consumer_key = 'UrjKcF93o1K8nPpRTVaR46M3b'
consumer_secret = 'zqXwrHxzcQj219W477abf2kTsNXNupZRbg9ZyJvKxZiPzaT90H'
access_token = '1374321478179581954-vwXT8LXDY4RU29lPNRVY56bTZVss5u'
access_token_secret = 'XHRd23nKpI0XUXu1Ki0V9XYS4yObMfMUAG2W8OswIyiqo'
# authorization of consumer key and consumer secret
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)

# set access to user's access key and access secret
auth.set_access_token(access_token, access_token_secret)

# calling the api
api = tweepy.API(auth)


def extract_entity_relation_sent(text, nlp):
    add = ['amp', 'via', 'cc', 'rt', 'dont', 'cant', 'doesnt', '&amp', 'youre']
    text = " ".join([word for word in text.split() if not word.lower() in add])

    doc = nlp(text.strip())

    head_entity = ''
    tail_entity = ''
    relation = ''

    name_entities = set([ent for ent in doc.ents])

    for tok in doc:
        for ent in name_entities:
            if tok.text in str(ent):
                if 'ubj' in tok.dep_:
                    head_entity = str(ent)
                    head_type = ent.label_
                if 'obj' in tok.dep_:
                    tail_entity = str(ent)
                    tail_type = ent.label_

        if tok.dep_ == 'ROOT' and tok.pos_ == 'VERB':
            relation = str(tok.text)

    if head_entity != '' and tail_entity != '' and relation != '':
        if head_entity != tail_entity:
            return (head_entity, relation, tail_entity, head_type, tail_type)
    else:
        return None


def extract_entity(text, nlp):
    sents = text.split('.')
    triple_list = []
    for sent in sents:
        triple = extract_entity_relation_sent(sent, nlp)
        if triple != None:
            triple_list.append(triple)

    return triple_list


def get_subject_object(sent, nlp):
    add = ['amp', 'via', 'cc', 'rt', 'dont', 'cant', 'doesnt', '&amp', 'youre']
    text = " ".join([word for word in sent.split() if not word.lower() in add])
    doc = nlp(text.strip())

    head_entity = ''
    tail_entity = ''
    relation = ''

    name_entities = set([ent for ent in doc.ents])

    for tok in doc:
        for ent in name_entities:
            if tok.text in str(ent):
                if 'ubj' in tok.dep_:
                    head_entity = str(ent)
                    head_type = ent.label_
                if 'obj' in tok.dep_:
                    tail_entity = str(ent)
                    tail_type = ent.label_

        if tok.dep_ == 'ROOT' and tok.pos_ == 'VERB':
            relation = str(tok.text)

    if head_entity != '' and tail_entity != '':
        if head_entity != tail_entity:
            return (head_entity, tail_entity)
def get_predicate(sent, nlp):
    doc = nlp(sent)
    roots = []
    tmp = ''
    try:
        for token in doc:
            if token.head == token and (token.pos_ == "VERB" or token.pos_ == "AUX"):
                roots.append(token)
        if roots == []:
            for token in doc.sents:
                roots.append(token.root)
        if roots == []:
            return ('')
        else:
            root = roots[0]

        for token in doc:
            if token.i == root.i + 1 and (token.dep_ == 'prep' or token.dep_ == 'agent' or token.dep_ == 'dative'):
                span = doc[root.i:token.i + 1]
                tmp = span.text
        for token in doc:
            if token.head.text == root.text and (token.dep_ == 'neg'):
                if token.i == root.i + 1:
                    if tmp != '':
                        predicate = tmp + ' not'
                    else:
                        predicate = root.text + ' not'
                elif token.i == root.i - 1:
                    if tmp != '':
                        predicate = 'not ' + tmp
                    else:
                        predicate = 'not ' + root.text
                return (predicate)
        if tmp == '':
            return (root.text)
        else:
            return (tmp.strip())
        return (root.text)
    except:
        return ('')


def get_object(sent, nlp):
    obj = ""
    doc = nlp(sent)
    roots = []
    count = 0
    rights_root = None
    lefts_root = None
    subject_dep = {"nsubj", "psubj", "csubj", "csubjpass", "nsubjpass"}
    object_dep = {"dobj", "iobj", "attr", "pobj", "acomp", "ccomp", "xcomp"}
    try:
        for token in doc:
            if token.head == token and (token.pos_ == "VERB" or token.pos_ == "AUX"):
                roots.append(token)
        if roots == []:
            for token in doc.sents:
                roots.append(token.root)
        if roots == []:
            return ("")
        else:
            root = roots[0]
        if list(root.lefts) != []:
            for rl in list(root.lefts):
                if rl.dep_ in subject_dep:
                    lefts_root = rl
                    break
        if lefts_root != None:
            span = doc[lefts_root.left_edge.i: lefts_root.right_edge.i + 1]
            with doc.retokenize() as retokenizer:
                retokenizer.merge(span)

        roots = []
        for token in doc:
            if token.head == token and (token.pos_ == "VERB" or token.pos_ == "AUX"):
                roots.append(token)
        if roots == []:
            for token in doc.sents:
                roots.append(token.root)
        if roots == []:
            return ("")
        else:
            root = roots[0]
        if list(root.rights) != []:
            for rl in list(root.rights):
                if rl.dep_ in object_dep:
                    rights_root = rl
                    break
        if rights_root != None:
            span = doc[rights_root.left_edge.i: rights_root.right_edge.i + 1]
            with doc.retokenize() as retokenizer:
                retokenizer.merge(span)
        for token in doc:
            if token.dep_ in object_dep:
                count += 1
        for token in doc:
            if count == 1:
                if token.dep_ in object_dep and token.i > root.i:
                    obj = token.text
            else:
                if token.dep_ in object_dep and (
                        token.head.text == root.text or token.head.text == doc[root.i + 1].text) and token.i > root.i:
                    obj = token.text
                    break
        if obj == '':
            for token in doc:
                if token.dep_ in object_dep and token.i > root.i:
                    obj = token.text
                    break
        if obj == '' and list(root.rights) != None and list(root.rights)[0].dep_ != 'punct' and token.i > root.i:
            obj = list(root.rights)[0].text
        for chunk in doc.noun_chunks:
            if chunk.root.text == obj:
                obj = doc[chunk.root.left_edge.i:chunk.root.right_edge.i + 1].text
        # print("objetc: ", obj, name_entities)
        #
        # for ent in name_entities:
        #     ent = ent.split()
        #     for e in ent:
        #         if e in obj:
        return (obj)
    except:
        return ("")


def extract_triple(text, nlp):
    sents = text.split('.')
    triple_list = []
    # print(text)
    for sent in sents:
        subj, obj = get_subject_object(sent, nlp)
        pred = get_predicate(sent, nlp)
        if subj != "":
            if pred != "":
                if obj != "":
                    triple = (subj, pred, obj)
                    triple_list.append(triple)
    return triple_list


def get_DBpedia_knowledge_graph(knowledge_graph):
    dbpedia_node = []
    dbpedia_kg = []
    related_knowledge = []

    # get list node is existing in dbpedia
    for element in knowledge_graph:
        check = element['is_new_knowledge'].split('-')
        if check[0] == 'false':
            raw_triples = dbpedia_query.get_link_DBpedia(element['subject'])
            for raw_triple in raw_triples:
                # triple = [[str(raw_triple['subject']), str(raw_triple['predicate']), str(raw_triple['object'])]]
                if element['subject'] == raw_triple['subject']:
                    related_knowledge.append({
                        'id': element['id'],
                        'tweet': element['tweet'],
                        'subject': str(raw_triple['subject']),
                        'predicate': str(raw_triple['predicate']),
                        'object': str(raw_triple['object']),
                        'created_at': element['created_at'],
                        'is_new_knowledge': 'false-db_pedia'
                    })
                if element['object'] == raw_triple['object']:
                    related_knowledge.append({
                        'id': element['id'],
                        'tweet': element['tweet'],
                        'subject': str(raw_triple['subject']),
                        'predicate': str(raw_triple['predicate']),
                        'object': str(raw_triple['object']),
                        'created_at': element['created_at'],
                        'is_new_knowledge': 'db_pedia-false'
                    })
            if element['subject'] not in dbpedia_node:
                dbpedia_node.append(element['subject'])
        if check[1] == 'false':
            raw_triples = dbpedia_query.get_link_DBpedia(element['object'])
            for raw_triple in raw_triples:
                if element['subject'] == raw_triple['subject']:
                    related_knowledge.append({
                        'id': element['id'],
                        'tweet': element['tweet'],
                        'subject': str(raw_triple['subject']),
                        'predicate': str(raw_triple['predicate']),
                        'object': str(raw_triple['object']),
                        'created_at': element['created_at'],
                        'is_new_knowledge': 'false-db_pedia'
                    })
                if element['object'] == raw_triple['object']:
                    related_knowledge.append({
                        'id': element['id'],
                        'tweet': element['tweet'],
                        'subject': str(raw_triple['subject']),
                        'predicate': str(raw_triple['predicate']),
                        'object': str(raw_triple['object']),
                        'created_at': element['created_at'],
                        'is_new_knowledge': 'db_pedia-false'
                    })
            if element['object'] not in dbpedia_node:
                dbpedia_node.append(element['object'])
    # print("check related kg")
    # print(related_knowledge)
    # get list relationships between nodes
    # for node in dbpedia_node:
    #     for new_node in dbpedia_node:
    #         kgs = []
    #         if new_node == node:
    #             continue
    #         else:
    #             kgs = dbpedia_query.get_relation(node, new_node)
    #             if kgs != []:
    #                 for kg in kgs:
    #                     dbpedia_kg.append(kg)
    return dbpedia_kg, related_knowledge


def get_timeline(time, score):
    if (time.__len__() != score.__len__()):
        raise Exception("Length of time and score is not match")
    newScore = []
    newScoreIndex = []
    tempData = []
    tempDataIndex = []
    for index in range(score.__len__()):
        if score[index] == 0:
            if tempData.__len__() != 0:
                newScore.append(tempData)
                newScoreIndex.append(tempDataIndex)
            tempData = []
            tempDataIndex = []
        else:
            tempData.append(score[index])
            tempDataIndex.append(index)
    # find timeline from newScoreIndex
    timeline = []
    for indices in newScoreIndex:
        timeline.append([
            time[indices[0]],
            time[indices[indices.__len__() - 1] + 1]
        ])

    return timeline


def extract_temporal_knowledge(group_knowledge, start_date, end_date):
    time_range = DateTimeRange(start_date, end_date)
    temporal_knowledge = []
    x_data_hour = []

    # for value in time_range.range(datetime.timedelta(minutes=1)):
    for value in time_range.range(datetime.timedelta(hours=1)):
        x_data_hour.append(value.strftime("%Y-%m-%d %H:%M"))
    mentioned_frequency = [0] * len(x_data_hour)
    diffuse_degree = [0] * len(x_data_hour)
    diffuse_sensitivity = [0] * len(x_data_hour)
    # time_option = 'minute'
    time_option = 'hour'
    group_tweets_id = []
    retweets_list = []
    tweet_id = []
    original_id = []
    for knowledge in group_knowledge:
        group_tweets_id.append(knowledge.tweet.id)
        tweet_id.append(knowledge.tweet.tweet_id)
        original_id.append(knowledge.tweet.original_tweet_id)
    for i in range(len(tweet_id)):
        try:
            if original_id[i] != 0:
                # status = api.get_status(id)
                # original_id = status.retweeted_status.id
                retweets = api.retweets(original_id[i], 100)
                for tweet in retweets:
                    retweets_list.append({
                        "tweet": tweet.text,
                        "id": tweet.id,
                        "created_at": tweet.created_at
                    })
            else:
                retweets = api.retweets(tweet_id[i], 100)
                for tweet in retweets:
                    retweets_list.append({
                        "tweet": tweet.text,
                        "id": tweet.id,
                        "created_at": tweet.created_at
                    })
        except:
            continue
    # print(len(retweets_list))
    if retweets_list != []:
        raw_diffuse_degree = event_detect.get_diffuse_degree(retweets_list, time_option=time_option)
        for x in x_data_hour:
            for xd in raw_diffuse_degree[0]:
                if x == xd:
                    diffuse_degree[x_data_hour.index((x))] = raw_diffuse_degree[1][raw_diffuse_degree[0].index(xd)]
    x_data_date, y_data = event_detect.get_tweet_distribution_kg(group_knowledge, time_option=time_option, keyword=None)
    for x in x_data_hour:
        for x_date in x_data_date:
            if x == x_date:
                mentioned_frequency[x_data_hour.index((x))] = y_data[x_data_date.index(x_date)]

    max_mf = max(mentioned_frequency)
    # print(len(retweets_list), max_mf, mentioned_frequency.index(max_mf))
    # for i in range(mentioned_frequency.index(max_mf), len(mentioned_frequency)):
    #     if mentioned_frequency[i] == 0:
    #         # end_time = i - 1
    #         end_time = i
    #         break
    # for i in range(mentioned_frequency.index(max_mf)):
    #     if mentioned_frequency[i] == 0:
    #         start_time = i + 1
    score = []
    for i in range(len(mentioned_frequency)):
        score.append(mentioned_frequency[i] + diffuse_degree[i])

    timeline = get_timeline(x_data_hour, score)
    # print("group_knowledge", group_knowledge)
    # print("y_data", y_data)
    temporal_knowledge.append({
        'tweet_id': group_knowledge[y_data.index(max(y_data))].tweet_id,
        'subject': group_knowledge[0].k_subject,
        'predicate': group_knowledge[0].k_predicate,
        'object': group_knowledge[0].k_object,
        'time_start': timeline[0][0],
        'time_end': timeline[len(timeline) - 1][1],
        'timeline': timeline,
        'occurrence': mentioned_frequency,
        'group_tweets_id': group_tweets_id,
        'diffuse_degree': diffuse_degree,
        'diffuse_sensitivity': diffuse_sensitivity,
        'mentions': sum(y_data),
    })
    return temporal_knowledge


def get_temporal_knowledge(keyword):
    unique_knowledge = Unique_knowledge.objects.filter(keyword=keyword)
    tweets_list = utils.get_tweet_in_time_range(pk=keyword, start_date='', end_date='', trend='')
    # knowledge_list = utils.extract_knowledge_graph(tweet_list)
    time = []
    for tweets in tweets_list:
        time.append(tweets.created_at)

    start_date = datetime_utils.correct_time(min(time).strftime("%Y-%m-%d %H"))
    end_date = datetime_utils.correct_time(max(time).strftime("%Y-%m-%d %H"))
    # count = 0
    for knowledge in tqdm(unique_knowledge):
        # count += 1
        # if count > 40:
        try:
            #     print()
            tmp_kg = Knowledge.objects.filter(keyword=keyword, k_subject=knowledge.k_subject,
                                              k_predicate=knowledge.k_predicate, k_object=knowledge.k_object)

            temporal_knowledge = extract_temporal_knowledge(tmp_kg, start_date=start_date, end_date=end_date)[0]
            tweet_obj = Tweet.objects.filter(id=temporal_knowledge['tweet_id'])
            # print(temporal_knowledge['tweet_id'])
            # print(tweet_obj[0])
            db_knowledge_subj = dbpedia_query.check_link_DBpedia(knowledge.k_subject)
            db_knowledge_obj = dbpedia_query.check_link_DBpedia(knowledge.k_object)
            if db_knowledge_subj:
                check_subj = 'true'
            else:
                check_subj = 'false'
            if db_knowledge_obj:
                check_obj = 'true'
            else:
                check_obj = 'false'
            check = check_subj + '-' + check_obj
            check_tkg = Temporal_knowledge.objects.filter(keyword=keyword, tweet=tweet_obj[0])
            if len(check_tkg) == 0:
                Temporal_knowledge.objects.create(
                    keyword=keyword,
                    tweet=tweet_obj[0],
                    k_subject=temporal_knowledge['subject'],
                    k_predicate=temporal_knowledge['predicate'],
                    k_object=temporal_knowledge['object'],
                    temporal_start=temporal_knowledge['time_start'],
                    temporal_end=temporal_knowledge['time_end'],
                    mentions=temporal_knowledge['mentions'],
                    is_new_knowledge=check,
                    occurrence=temporal_knowledge['occurrence'],
                    timeline=temporal_knowledge['timeline'],
                    group_tweets_id=temporal_knowledge['group_tweets_id'],
                    diffuse_degree=temporal_knowledge['diffuse_degree'],
                    diffuse_sensitivity=temporal_knowledge['diffuse_sensitivity'],
                )
            else:
                Temporal_knowledge.objects.filter(keyword=keyword, tweet=tweet_obj[0]).update(
                    keyword=keyword,
                    tweet=tweet_obj[0],
                    k_subject=temporal_knowledge['subject'],
                    k_predicate=temporal_knowledge['predicate'],
                    k_object=temporal_knowledge['object'],
                    temporal_start=temporal_knowledge['time_start'],
                    temporal_end=temporal_knowledge['time_end'],
                    mentions=temporal_knowledge['mentions'],
                    is_new_knowledge=check,
                    occurrence=temporal_knowledge['occurrence'],
                    timeline=temporal_knowledge['timeline'],
                    group_tweets_id=temporal_knowledge['group_tweets_id'],
                    diffuse_degree=temporal_knowledge['diffuse_degree'],
                    diffuse_sensitivity=temporal_knowledge['diffuse_sensitivity'],
                )
        except:
            continue
    # return True
