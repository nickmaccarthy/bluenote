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

class QueryException(Exception):
    pass

class Query(object):


    def __init__(self, query, index='logstash*', start=None, end=None, exclude=None):
        if start is not None or end is not None:
            self.times = self.create_time(start, end)
        self.index = index
        self.query_raw = query
        self.qd = self.get_intentions(self.query_raw)
        self.build_es_query(self.qd, self.times, exclude)


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
            if bluenote.find_in_list('terms', query_parts):
                qd['agg_type'] = 'terms'
                qd['agg_opts'] = {}
                qd['agg_opts'] = self.build_terms(bluenote.find_in_list('terms', query_parts))
            if bluenote.find_in_list('fields', query_parts):
                qd['fields'] = self.build_fields(bluenote.find_in_list('fields', query_parts)) 
                
        else:
            qd['query_opts'] = self.build_main_query(query_base)
            qd['fields'] = ['*'] 

        return qd

    def build_fields(self, string):
        field_str = None
        if re.match("fields (.*?)", string):
            field_match = re.search("fields (.*?)$", string)
            if field_match.group(1):
                field_str = field_match.group(1)

        if field_str:
            fields = [ x.strip() for x in field_str.split(',') ]

            return fields

        return ['*']

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

        thed = { 'args': args, 'agg_type': module, 'agg_field': bluenote.clean_keys(field), 'by': by }  
        return thed

    def build_terms(self, string):
        parts = string.split(" ")
        args = {}
        for part in parts:
            if ":" in part:
                key, val = part.split(":")
                args[key] = val
            elif "=" in part:
                k,v = part.split("=")
                args[k] = v

            
        term_field = args.get('field')
        if not term_field:
            raise QueryException('Unable to define term field.  This is a required')
            return None
        
        term_size = args.get('size', 5)
        term_orderby = args.get('order_by', '_count')
        term_direction = args.get('sort', 'desc') 

        thed = { 'args': args, 'agg_type': 'terms', 'by': args.get('field'), 'size': term_size, 'order_by': { 'field': term_orderby, 'direction': term_direction }}  
        return thed

    def build_main_query(self, lquery):
        if '_type' in lquery:
            m = re.search('_type:(.*?)\s*', lquery)
            _type = m.group(0)
        else:
            _type = None

        index = self.index.strip('*')

        return { '_type': _type, 'index': index, 'args': lquery }
        

    def build_es_query(self, qd, times, exclude):
  
        _from = bluenote.epoch2iso(times['start'])
        _to = bluenote.epoch2iso(times['end'])
       
        self.queryd = {}
        self.queryd['lucene'] = qd['query_opts']['args']
        
        if exclude is None:
            exclude = ''
        else:
            exclude = exclude
                  

        self.queryd['es_query'] = {
            "query": {
                "filtered": {
                    "filter": {
                        "bool": {
                            "must": [
                                {   
                                    "range": { 
                                        "@timestamp": { "from": times['start_datemath'], "to": times['end_datemath'] }
                                    }
                                },
                                {
                                    "query": {
                                        "query_string": {
                                            "query": qd['query_opts']['args']
                                        }
                                    }
                                }
                            ],
                            "must_not": {
                                "query": {
                                    "query_string": {
                                        "query": exclude
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        # Filter our only fields we want to see
        if qd.get('fields') is not None:
            self.queryd['es_query'].update(
            {
                "_source": {
                    "include": qd['fields'],
                }
            })
        if bluenote._get(qd, '', 'agg_type') == 'date_histogram': 
            self.queryd['es_query'].update( 
            {
                "size": 0,
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
        if bluenote._get(qd, '', 'agg_type') == 'terms':
            self.queryd['es_query'].update(
            {
                "size": 0,
                "aggs": {
                    "events_by_%s" % qd['agg_opts']['by']: {
                        "terms": {
                            "field": qd['agg_opts']['by'],
                            "size": qd['agg_opts']['size'],
                            "order": {
                                qd['agg_opts']['order_by']['field']: qd['agg_opts']['order_by']['direction']
                            }

                        }
                    }
                }
            })

        
if __name__ == "__main__":
    q = Query("index=logstash* _type:system_stats | date_histogram avg:current_load by host interval=30s")
