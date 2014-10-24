import sys
import os
import re
import datetime
import time

from pprint import pprint

'''
    Script for removing bluenote-int docs
'''
BN_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.environ['BN_HOME'] = str(BN_HOME)
sys.path.append(os.path.join(BN_HOME, 'lib'))
# Import our conf path
sys.path.append(os.path.join(BN_HOME, 'etc', 'conf'))

from elasticsearch import Elasticsearch
import bluenote
from bluenote.search import Search
from bluenote.search.query import Query
import bluenote.filter
import bluenote.alert
from config import Config
import yaml

from alerts import alerts

es = Elasticsearch(['dfweshm01:9200'])
s = Search()
logger = bluenote.get_logger('search-test')

triggered_alerts = es.search(index='bluenote-int', doc_type='alert_trigger')

alert_name = "High Average Query Time"

ids = []
for ta in triggered_alerts['hits']['hits']:
    ids.append(ta['_id'])
    print "ID: %s - Name: %s, Last Run: %s" % (ta['_id'], ta['_source']['alert-name'], ta['_source']['time'])

if len(ids) > 0:
    print "Deleting 'em"

    for id in ids:
        print es.delete('bluenote-int', 'alert_trigger', id)
    
