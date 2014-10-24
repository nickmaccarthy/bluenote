import sys
import os
import datetime
import time
import calendar
import dateutil
from dateutil.relativedelta import relativedelta
from elasticsearch import Elasticsearch
import bluenote
from bluenote.search.query import Query
import re
import json
import operator
import collections
from pprint import pprint

def date_histogram(res):
    intentions = res['intentions']
    events_by = 'events_by_%s' % intentions['qd']['agg_opts']['by']
    agg_type = intentions['qd']['agg_opts']['agg_type']
    agg_field = intentions['qd']['agg_opts']['agg_field']

    rd = {}
    rd['_results'] = {}
    for results in res['_results']['aggregations'][events_by]['buckets']:
        mres = []
        for r in results['events_by_date']['buckets']:
            val_key = "%s_%s" % (agg_type, agg_field)
            mres.append({'time': r['key_as_string'], 'value': r[val_key]['value']})
        rd['_results'][results['key']] = mres
    rd['query_intentions'] = intentions
    return rd

def result_set(results):
    retd = {}
    retd['query_intentions'] = results['intentions']
    mres = []
    for r in results['_results']['hits']['hits']:
        mres.append(bluenote.flatten_dict(r))
    retd['_results'] = mres 
    return retd

def meets_threshold(results, threshold):
    m = re.match("(?P<intended_operator>\w+) (?P<measure>\d+)$", threshold)
    intended_operator = m.group("intended_operator")
    measure = int(m.group("measure"))

    if "ge" in intended_operator:
        op = operator.__ge__ 
    elif "gt" in intended_operator:
        op = operator.__gt__
    elif "le" in intended_operator:
        op = operator.__le__
    elif "eq" in intended_operator:
        op = operator.eq

    returnd = {}
    returnd['query_intentions'] = results['query_intentions']
    alerts = []
    for main_key, values in results['_results'].iteritems():
        for v in values:
            if op(v['value'], measure):
                alerts.append({'key': main_key, 'value': v['value'], 'time': v['time']})
    returnd['_results'] = alerts

    return returnd

     
