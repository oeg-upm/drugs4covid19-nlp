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
import time

solr = pysolr.Solr('https://librairy.linkeddata.es/data/covid', timeout=30)

def get_document(file_url):
    with open(file_url) as f:
      license = file_url.split("/")[5]
      data = json.load(f)
      document = {}
      id = data['paper_id']
      results = solr.search("id:"+id)
      for result in results:
          return result
      document['id']=id
      metadata = data['metadata']
      document['name_s']=metadata['title']
      document['source_s']=license
      document['url_s']="https://cord-19.apps.allenai.org/paper/"+str(id)
      return document


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
        documents = pool.map(get_document, [directory_path + "/" + file for file in files[min:max]])
        print("[",datetime.now(),"]","indexing",len(documents)," docs...")
        try:
            solr.add(documents)
            solr.commit()
        except:
            print("Solr query error. Wait for 5secs..")
            time.sleep(5.0)
            solr.commit()
        counter=max

print(counter,"docs added")
pool.close()
