#!/usr/bin/env python3
# docker run -d -p 6200:5000 librairy/bio-nlp:latest
import tarfile
import urllib.request
import json
import requests
import pysolr
import os
import multiprocessing as mp
from datetime import datetime
import time

initial = 0

# librAIry Bio-NLP Endpoint
#API_ENDPOINT = "http://localhost:5000/bio-nlp/diseases"
#API_ENDPOINT = "http://localhost:6200/bio-nlp/diseases"
BIONLP_ENDPOINT = "http://localhost:6200/bio-nlp"
#BIONLP_ENDPOINT = "http://localhost:5000/bio-nlp"

# Setup a Solr instance. The timeout is optional.
solr = pysolr.Solr('http://librairy.linkeddata.es/data/covid-paragraphs', timeout=2)

def get_annotations(annotation,text):
    data = {}
    data['text']=text
    json_request = json.dumps(data)
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    api_endpoint = BIONLP_ENDPOINT+"/"+annotation
    response = requests.post(url = api_endpoint, data = json_request, headers=headers)
    #convert response to json format
    try:
        annotations =  response.json()
        return annotations
    except:
        print("No response from get_diseases")
        return []

def annotate(annotation_type,document):
    codes, names = {}, {}
    for code in range(0,11):
        codes[code] = []
        names[code] = []
    text = document['text_t']
    for annotation in get_annotations(annotation_type,text):
        #print(annotation_type,annotation,"found")
        if ("level" in annotation):
            level = int(annotation["level"])
            code_value = 'nan'
            if ('code' in annotation):
                code_value = annotation['code']
            if ('atc_code' in annotation):
                code_value = annotation['atc_code']
            if (code_value != 'nan'):
                codes[level].append(code_value)
            name_value = annotation["name"].lower()
            if (len(name_value) > 0):
                names[level].append(name_value)
    for code in codes:
        if (len(codes[code]) > 0):
            document['bionlp_'+annotation_type+"_C"+str(code)]= list(set(codes[code]))
    for name in names:
        if (len(names[name]) > 0):
            document['bionlp_'+annotation_type+"_N"+str(name)]= list(set(names[name]))
    #print(annotated_paragraph)
    return document


def get_document(paragraph):
    if (not 'text_t' in paragraph):
        return paragraph
    document = {}
    document['id'] = paragraph['id']
    document['section_s'] = paragraph['section_s']
    document['text_t'] = paragraph['text_t']
    document['article_id_s'] = paragraph['article_id_s']
    document['size_i'] = paragraph['size_i']
    annotate("diseases",document)
    annotate("drugs",document)
    return document

def get_solr_query(annotation_type):
    return ["!bionlp_"+annotation_type+"_N"+str(i)+":[* TO *]" for i in range(0,11)]

pool = mp.Pool(8)

counter = 0
completed = False
window_size=250
cursor = "*"
filters = [get_solr_query('drugs'),get_solr_query('diseases')]
while (not completed):
    old_counter = counter
    #solr_query = " AND ".join([y for x in filters for y in x])
    solr_query = "*:*"
    try:
        print(solr_query)
        paragraphs = solr.search(q=solr_query,rows=window_size,cursorMark=cursor,sort="id asc")
        cursor = paragraphs.nextCursorMark
        counter += len(paragraphs)
        documents = pool.map(get_document, paragraphs)
        solr.add(documents)
        solr.commit()
        print("[",datetime.now(),"] solr index updated! ",counter)
        if (old_counter == counter):
            print("done!")
            break
    except Exception as e:
        print("error:",e)
        print("Solr query error. Wait for 5secs..")
        time.sleep(5.0)
        solr.commit()

print(counter,"paragraphs successfully annotated with MESH-Diseases")
pool.close()
