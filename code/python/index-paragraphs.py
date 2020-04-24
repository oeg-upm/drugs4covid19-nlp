#!/usr/bin/env python3
import tarfile
import urllib.request
import json
import requests
import pysolr
import os
import multiprocessing as mp
from datetime import datetime
import hashlib

solr = pysolr.Solr('https://librairy.linkeddata.es/data/covid-paragraphs', timeout=10)

cord19_url = "https://cord-19.apps.allenai.org/paper/"
unknown_section = "(which was not peer-reviewed)"

def get_document(id,json_paragraph):
    document = {}
    section = json_paragraph['section'].lower()
    if (section == unknown_section or len(section) == 0):
        section = "body"
    document['section_s'] = section
    text = json_paragraph['text']
    document['text_t'] = text
    text_content = id + text + section
    hash_object = hashlib.md5(text_content.encode())
    document['id'] = hash_object.hexdigest()
    document['article_id_s'] = id
    document['size_i'] = len(text)
    return document

def get_documents(file_url):
    with open(file_url) as f:
      license = file_url.split("/")[4]
      data = json.load(f)
      documents = []
      id = data['paper_id']
      results = solr.search("id:"+id)
      if (len(results) > 0):
            print("Found",document["id"])
            return results
      if ('abstract' in data):
          for abstract in data['abstract']:
              documents.append(get_document(id,abstract))
      if ('body_text' in data):
          for paragraph in data['body_text']:
              documents.append(get_document(id,paragraph))
      #print(len(documents), "paragraphs retrieved from paper: ", id)
      return documents


# Articles
directories = [
    ("/Users/cbadenes/Downloads/covid19/custom_license/pdf_json","custom_license"),
    ("/Users/cbadenes/Downloads/covid19/custom_license/pmc_json","custom_license"),
    ("/Users/cbadenes/Downloads/covid19/comm_use_subset/pmc_json","commercial_use"),
    ("/Users/cbadenes/Downloads/covid19/comm_use_subset/pdf_json","commercial_use"),
    ("/Users/cbadenes/Downloads/covid19/biorxiv_medrxiv/pdf_json","biorxiv"),
    ("/Users/cbadenes/Downloads/covid19/noncomm_use_subset/pmc_json","noncommercial_use"),
    ("/Users/cbadenes/Downloads/covid19/noncomm_use_subset/pdf_json","noncommercial_use")
]

pool = mp.Pool(4)

for directory in directories:
    print("Indexing directory", directory)
    directory_path = directory[0]
    files = os.listdir(directory_path)
    min = 0
    max = 0
    incr = 500
    counter = 0
    while(max < len(files)):
        min = counter
        max = min + incr
        if (max > len(files)):
            max = len(files)
        documents = pool.map(get_documents, [directory_path + "/" + file for file in files[min:max]])
        commit_documents = [paragraph for paragraphs in documents for paragraph in paragraphs]
        print("[",datetime.now(),"]","indexing",len(commit_documents)," docs...")
        try:
            solr.add(commit_documents)
            solr.commit()
        except:
            print("Solr query error. Wait for 5secs..")
            time.sleep(5.0)
            solr.commit()
        counter=max

print(counter,"docs added")
pool.close()
