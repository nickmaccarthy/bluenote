#!/usr/local/bin/python
import sys
import os
import re
import datetime
import time
import signal
import Queue
import threading

from pprint import pprint

BN_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.environ['BN_HOME'] = str(BN_HOME)

activate_this = os.path.join(BN_HOME, 'env', 'bin', 'activate_this.py')
execfile(activate_this, dict(__file__=activate_this))

sys.path.append(os.path.join(BN_HOME, 'lib'))
# Import our conf path
sys.path.append(os.path.join(BN_HOME, 'etc', 'conf'))

from elasticsearch import Elasticsearch
import bluenote
from bluenote.search import Search
from bluenote.search.query import Query
import bluenote.filter
import bluenote.alert
import bluenote.workers

# Conf loading
from alerts import alerts
from bn import bncfg 
from bn_mail import mailcfg

try:
    es = Elasticsearch(bncfg['esh_server'])
except Exception, e:
    logger.exception("Unable to connect to ES server! Reason: %s" % (e))
    sys.exit()

s = Search()
logger = bluenote.get_logger('bnd')
#eslogger = bluenote.get_logger('elasticsearch')
#estracelogger = bluenote.get_logger('elasticsearch.trace')

es.indices.create(index='bluenote-int', ignore=400)

q = Queue.Queue()

def worker(q, alert):
    workit = bluenote.workers.bnd(es, alert)
    q.task_done()
    try:
        q.get(timeout=2)
    except Exception, e:
        logger.exception('Queue timeout when getting thread: %s, alert: %s ' % (e, alert))       


def main():
    for alert in range(len(alerts)):
        q.put(alert)

    for alert in alerts:
        t = threading.Thread(target=worker, args=(q, alert))
        t.start()
        logger.info('starting search for %s' % (alert['name']))

    q.join() 


if __name__ == "__main__":
    logger.info("bluenoted has started")
    main()
    logger.info("bluenoted has ended")
