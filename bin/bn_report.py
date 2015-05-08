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
import bluenote.report
import bluenote.workers

# Conf loading
from reports import reports 
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

def get_report(name):
    return (item for item in reports if item["name"] == name).next()

def main(argv):
    report_name = argv[0]

    if not report_name:
        print "You need to specify a report name"
        sys.exit()
    report = get_report(report_name)
    if report:
        res = s.query(report['query'], _from=report.get('earliest_time', '-24h'), _to=report.get('latest_time', 'now'))
        report_results = bluenote.filter.result_set(res)
        result_len = len(report_results['_results'])
   
        #pprint(report_results['_results'])
        csv_file = bluenote.makecsvfromlist(report_results['_results'], filename=report['name'])

        # email it
        email_subject = 'Bluenote Report: {0}'.format(report['name'])
        email_it = bluenote.report.email(report['email']['to'], report['name'], csv_file, res, subject=email_subject)
        
if __name__ == "__main__":
    main(sys.argv[1:])
