import sys
import os
import datetime
import time
import calendar
import dateutil
from dateutil.relativedelta import relativedelta
from elasticsearch import Elasticsearch
import bluenote
import re
import json

from pprint import pprint

class Query(object):


    def __init__(self, query, index='logstash*', start=None, end=None):
        if start is not None or end is not None:
            self.times = self.create_time(start, end)
        self.index = index
        self.query_raw = query
        self.qd = self.get_intentions(self.query_raw)
        self.build_es_query(self.qd, self.times)


    def create_time(self, start, end):
        now = time.time()
        intervals = { 
            's' : 0,
            'm' : 60,
            'h' : 3600,
            'd' : 86400,
            'W' : 604800,
            'M' : 2419200
        }
        ts = { 'start': start, 'end': end }
        new = {}
        new['start_relative'] = start
        new['start_datemath'] = "%s%s" % ( end, start )
        new['end_datemath'] = end
        new['end_relative'] = end
        for k,v in ts.iteritems():
            m = re.match("^(?P<time>\-\d+|\d+)(?P<interval>\w+)", v)
            if m:
                _time = m.group('time')
                interval = m.group('interval')
                if '-' in _time:
                    _time_multiplier = int(_time.lstrip('-'))
                    interval_seconds = intervals.get(interval, 0)
                    back =  _time_multiplier * interval_seconds
                    newtime = now - back
                    new[k] = newtime    
                    new['start_iso'] = bluenote.epoch2iso(newtime)
            elif 'now' in v:
                now = time.time() 
                end = now
                new[k] = now
                new['end_iso'] = bluenote.epoch2iso(now)
        return new

        
    def get_intentions(self, query):
        query_parts = None
        qd = {}
        if "|" in query:
            query_parts = query.split("|")
            query_base = query_parts[0]
        else:
            query_base = query

        if query_parts:
            query_parts = [ q.strip() for q in query_parts ]
            qd['query_opts'] = {}
            qd['query_opts'] = self.build_main_query(query_parts[0])
            if bluenote.find_in_list('date_histogram', query_parts):
                qd['agg_type'] = 'date_histogram'
                qd['agg_opts'] = {}
                qd['agg_opts'] = self.build_date_histogram(  bluenote.find_in_list('date_histogram', query_parts))
        else:
            qd['query_opts'] = self.build_main_query(query_base)

        return qd


    def build_date_histogram(self, string):
        parts = string.split(" ")
       
        if re.match(".*by\s+([\w,]+)", string):
            by = re.search(".*by\s+([\w,]+)", string)
            if by.group(1):
                by = by.group(1)

        args = {}
        for part in parts:
            if ":" in part:
                module, field = part.split(":")
            elif "=" in part:
                k,v = part.split("=")
                args[k] = v

        return { 'args': args, 'agg_type': module, 'agg_field': bluenote.clean_keys(field), 'by': by }  

    def build_main_query(self, lquery):
        if '_type' in lquery:
            m = re.search('_type:(.*?)\s*', lquery)
            _type = m.group(0)

        index = self.index.strip('*')

        return { '_type': _type, 'index': index, 'args': lquery }
        

    def build_es_query(self, qd, times):
  
        _from = bluenote.epoch2iso(times['start'])
        _to = bluenote.epoch2iso(times['end'])
       
        self.queryd = {}
        self.queryd['lucene'] = qd['query_opts']['args']

              
        self.queryd['es_query'] = {
            "query": {
                "filtered": {
                    "filter": {
                        "bool": {
                            "must": [
                                {   
                                    "range": { 
                                        "@timestamp": { "from": times['start_datemath'], "to": times['end_datemath'] }
                                        #"@timestamp": { "from": _from, "to": _to }
                                        #"@timestamp": { "from": "now-1m", "to": "now" }
                                        #"@timestamp": { "from": times['start'], "to": times['end'] }
                                    }
                                },
                                {
                                    "query": {
                                        "query_string": {
                                            "query": qd['query_opts']['args']
                                        }
                                    }
                                }
                            ] 
                        }
                    }
                }
            }
        }

        if bluenote._get(qd, '', 'agg_type') == 'date_histogram': 
            self.queryd['es_query'].update( 
            {
                "aggs": {
                    "events_by_%s" % qd['agg_opts']['by']: {
                        "terms": { 
                            "field": "%s.raw" % qd['agg_opts']['by']
                        },
                        "aggs": {
                            "events_by_date": {
                                "date_histogram": {
                                    "field": "@timestamp", 
                                    "interval": qd['agg_opts']['args']['interval'] 
                                },
                                "aggs": {
                                    "%s_%s" % (qd['agg_opts']['agg_type'], qd['agg_opts']['agg_field']) : {
                                        qd['agg_opts']['agg_type']: {
                                            "field": qd['agg_opts']['agg_field']
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            })
        #else:
        #    # Makes a standard query
        #    self.queryd['es_query'] = {
        #        "query": {
        #            "bool": {
        #                "must": [
        #                    {   
        #                        "range": { 
        #                            "@timestamp": { "from": _from, "to": _to }
        #                        }
        #                    },
        #                ] 
        #            }
        #        }
        #    }

if __name__ == "__main__":
    q = Query("index=logstash* _type:system_stats | date_histogram avg:current_load by host interval=30s")
