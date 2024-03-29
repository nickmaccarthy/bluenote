#!/usr/local/bin/python
import sys
import os
import re
import datetime
import time

from pprint import pprint

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

es.indices.create(index='bluenote-int', ignore=400)

for alert in alerts:
    should_alert = False
    if alert.get('disabled') == 1: continue

    #nag_threshold = bluenote.relative_time_to_seconds( bluenote._get(alert, 0, 'alert', 'threshold') )

    #if bluenote.alert.last_run(es, alert['name']) > 0:
    #    time_since = ( bluenote.get_current_time_local() - bluenote.alert.last_run(es, alert['name']))
    #    if time_since <= nag_threshold: 
    #        # No need to go any further, we havent hit our threshold yet
    #        continue

    try:
        res = s.query(alert['query'], _from=alert.get('earliest_time', '-1m'), _to=alert.get('latest_time', 'now'))
    except Exception, e:
        print "Unable to query: %s" % e
        continue

    ## For aggregated results
    if res['intentions']['qd'].has_key('agg_type'):
        intentions = res.get('intentions', None)
        agg_intention = bluenote._get(intentions, None, 'qd', 'agg_type')

        if agg_intention:
            threshold = "%s %s" % ( alert['alert']['relation'], alert['alert']['qty'] )
            
            if 'date_histogram' in agg_intention:
                results = bluenote.filter.date_histogram(res)
                alert_results = bluenote.filter.meets_threshold(results, threshold)
                if len(alert_results['_results']) >= 1:
                    should_alert = True

    else:
    ## For just a standard result set
        alert_results = bluenote.filter.result_set(res)
        
        if len(alert_results['_results']) > 0:
            should_alert = True
            #bluenote.alert.email( alert['alert']['action']['email_to'], results, alert['name'], subject="Blunote Alert: %s" % alert['name'])
    if should_alert:
            print "Alerting!"
            email_subject = 'Bluenote Alert: %s' % alert['name']
            print email_subject
            email_it = bluenote.alert.email( alert['alert']['action']['email_to'], alert_results, alert['name'], subject=email_subject ) 
            email_it = True
            if email_it:
                logger.info("""msg="%s", email_to="%s", name="%s", subject="%s" """ % ( "Email Sent", alert['alert']['action']['email_to'], alert['name'], email_subject ))
                #es.index(index='bluenote-int', doc_type='alert_trigger', id=alert['name'], body={'alert-name': alert['name'], 'time': bluenote.get_current_utc(), 'results': alerts})

                SCRIPT_DIRS = bluenote.get_bindirs(BN_HOME)
                print SCRIPT_DIRS
                if alert['alert']['action'].has_key('script'):
                    print bluenote.run_script(alert['alert']['action']['script']['filename'], alert_results)
                #elif alert['alert']['action'].has_key('pymod'):
                #    print bluenote.run_

