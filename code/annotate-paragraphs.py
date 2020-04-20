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
API_ENDPOINT = "http://localhost:6200/bio-nlp/drugs"

# Setup a Solr instance. The timeout is optional.
solr = pysolr.Solr('http://librairy.linkeddata.es/data/covid-paragraphs', timeout=2)

def get_diseases(text):
    data = {}
    data['text']=text
    json_request = json.dumps(data)
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    response = requests.post(url = API_ENDPOINT, data = json_request, headers=headers)
    #convert response to json format
    try:
        diseases =  response.json()
        return diseases
    except:
        print("No response from get_diseases")
        return []

def get_document(annotated_paragraph):
    if (not 'text_t' in annotated_paragraph):
        return annotated_paragraph
    codes = {}
    for code in range(1,11):
        codes[code] = []
    paragraph = annotated_paragraph['text_t']
    for disease in get_diseases(paragraph):
        #print(disease,"found")
        if ("level" in disease):
            level = int(disease["level"])
            codes[level].append(disease["name"].lower())
    for code in codes:
        if (len(codes[code]) > 0):
            annotated_paragraph['bionlp_disease'+str(code)]= list(set(codes[code]))
    #print(annotated_paragraph)
    return annotated_paragraph


pool = mp.Pool(4)

counter = 0
completed = False
window_size=100
cursor = "*"
while (not completed):
    old_counter = counter
    solr_query = " AND ".join(["!bionlp_disease"+str(i)+"_t" for i in range(1,11)])
    try:
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
    except:
        print("Solr query error. Wait for 5secs..")
        time.sleep(5.0)
        solr.commit()

print(counter,"paragraphs successfully annotated with MESH-Diseases")
pool.close()
