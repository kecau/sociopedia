from SPARQLWrapper import SPARQLWrapper, JSON
import string

sparql = SPARQLWrapper("http://dbpedia.org/sparql")
import requests


def link_entity(entity, entity_type, limit):
    entity = entity.replace(" ", "_")
    sparql.setQuery(
        """
        SELECT distinct *

        WHERE { 

        ?entity rdfs:label ?name 
        FILTER (bif:contains(?name, "%s"))

        }

        LIMIT %d
        """ % (entity, limit)
    )

    d = {}
    sparql.setReturnFormat(JSON)
    #     print(sparql.query().convert())
    try:
        results = sparql.query().convert()
        for result in results["results"]["bindings"]:
            tmp = result["name"]["value"]
            if len(entity) == len(tmp):
                d[result["entity"]["value"]] = tmp
                break
            elif entity.lower() in tmp.lower().split():
                d[result["entity"]["value"]] = tmp
    #                 break
    except Exception as e:
        print("error search dbpedia", e)

    return d


def entity_relate_object(entity):
    sparql.setQuery(
        """
        SELECT distinct *

        WHERE { 

        <%s> ?predicate ?object

        }
        """ % (entity)
    )

    d = {}
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
        for result in results["results"]["bindings"]:
            object_type = result["object"]["type"]
            object_value = result["object"]["value"]

            lang = None
            if "xml:lang" in result["object"]:
                lang = result["object"]["xml:lang"]

            if lang is None or lang == 'en':
                if object_type != 'uri' and len(object_value) < 100:
                    predicate = result["predicate"]["value"].split('/')[-1]
                    #                     print(result["predicate"]["value"])
                    if predicate != 'wikiPageID' and predicate != 'wikiPageRevisionID' and predicate != 'wikiPageLength':
                        d[predicate] = object_value
    except Exception as e:
        print("error entity_relate_object", e, entity)

    return d


def check_link_DBpedia(entity):
    prefix = 'https://dbpedia.org/data/'
    new_entity = '_'.join(entity.split())
    url = prefix + new_entity + '.json'
    try:
        resp = requests.get(url)
        data = resp.json()
        if data != {}:
            return False
        return True
    except:
        return False
def get_link_DBpedia(entity):
    prefix = 'https://dbpedia.org/data/'
    entity = '_'.join(entity.split())
    url = prefix + entity + '.json'
    resp = requests.get(url)
    triples = []
    not_in = ['wikiPageRevisionID', 'wikiPageLength', 'hypernym', 'reason', 'wikiPageID',
              'wikiPageUsesTemplate', 'wikiPageRedirects', 'wikiPageDisambiguates', 'prov#wasDerivedFrom',
              'rdf-schema#label', 'abstract', '#', 'comment', 'wikiPageLength', 'rdf-schema#seeAlso']
    data = resp.json()
    if data != {}:
        for row in data.keys():
            tmp_object = row.split('/')
            subject_value = str(tmp_object[len(tmp_object) - 1].replace("_", " "))
            for key in data[row].keys():
                tmp_predicate = key.split('/')
                predicate = str(tmp_predicate[len(tmp_predicate) - 1])
                if data[row][key][0]['type'] == 'uri':
                    tmp_object = data[row][key][0]['value'].split('/')
                    object_value = str(tmp_object[len(tmp_object) - 1].replace("_", " "))
                else:
                    object_value = str(data[row][key][0]['value'])
                if predicate not in not_in and len(subject_value) < 100 and len(object_value) < 100 and subject_value != object_value:
                    triples.append({
                        'subject': subject_value,
                        'predicate': predicate,
                        'object': object_value
                    })
                if len(triples) > 10:
                    return triples
    return triples

def get_relation(entity1, entity2):
    entity1 = '_'.join(entity1.split())
    entity2 = '_'.join(entity2.split())
    sparql.setQuery(
        """
        SELECT ?resource1 ?p1 ?intermediary ?p2 ?resource2
            WHERE
            {
              VALUES ?resource1 { dbr:%s}
              VALUES ?resource2 { dbr:%s}
              FILTER(?resource1 != ?resource2)

              {
                ?resource1 ?p1 ?resource2
              }
              UNION
              {
                ?resource1 ?p1 ?intermediary.
                ?intermediary ?p2 ?resource2.
              }
            }

        """ % (entity1, entity2)
    )

    d = []
    sparql.setReturnFormat(JSON)
    #     print(sparql.query().convert())
    try:
        results = sparql.query().convert()
        #         print(results["results"]["bindings"])
        for result in results["results"]["bindings"]:
            if 'intermediary' in result.keys():

                d.append({
                    'subject': entity1.replace('_', ' '),
                    'predicate': result['p1']['value'].split('/')[-1].replace('_', ' '),
                    'object': result['intermediary']['value'].split('/')[-1].replace('_', ' ')
                })
                d.append({
                    'subject': result['intermediary']['value'].split('/')[-1].replace('_', ' '),
                    'predicate': result['p2']['value'].split('/')[-1].replace('_', ' '),
                    'object': entity2.replace('_', ' ')
                })
            else:

                d.append({
                    'subject': entity1.replace('_', ' '),
                    'predicate': result['p1']['value'].split('/')[-1].replace('_', ' '),
                    'object': entity2.replace('_', ' ')
                })

    except Exception as e:
        print("error", e)
    return d
