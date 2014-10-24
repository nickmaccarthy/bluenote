import sys
import os
import re
import datetime
import time

from pprint import pprint

'''
    Script for testing out a search in the BNQL
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


es = Elasticsearch(['dfweshm01:9200'])

s = Search()

our_query = sys.argv[1]
try:
    #res = s.query("index=logstash* _type=mysql_processlist_stats | date_histogram avg:avg_query_time by host interval=30s", _from="-1m", _to="now")
    res = s.query(our_query, _from="-1m", _to="now")
    pprint(res)
except Exception, e:
    print "Unable to query: %s" % e


