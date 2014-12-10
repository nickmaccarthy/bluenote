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
import bluenote.result
import re
import json

from bn import bncfg

logger = bluenote.get_logger('bluenote.search.Search')

class Search(object):


    def __init__(self):
       self.es = Elasticsearch(bncfg['esh_server'])
       self.set_indexes() 


    def set_indexes(self):
        indices = self.es.indices.stats("_all")['indices']
        self.indexes = []
        self.time_indexes = []
        for i in indices:
            if '-' in i:
                self.time_indexes.append(self.time_index(i))
            self.indexes.append(i)

   
    def query(self, query, **qargs):
        _from = qargs.get('_from', '-1m')
        _to = qargs.get('_to', 'now')
        index = qargs.get('index', 'logstash')
        index = index.strip('*')
        filters = qargs.get('filters', '')
        exclude = qargs.get('exclude', None)

        search_indexes = self.find_indexes((self.format_relative_time(_from), self.format_relative_time(_to)), index)
        search_indexes = ''.join(search_indexes)

        qobj = Query(query, index, _from, _to, exclude)

        lucene_query = None
        if qobj.queryd['lucene']:
            lucene_query = qobj.queryd['lucene'] 

        returnd = {}
        returnd['search_indexes'] = ', '.join(search_indexes)
        returnd['intentions'] = vars(qobj)
        try:
            returnd['_results'] = self.es.search(
                                    index=search_indexes, 
                                    body=qobj.queryd['es_query'],
                                    timeout="10"
                                )
        except Exception, e:
            logger.exception('Unable to run query from search module: %s' % (e))
            raise 

        return bluenote.result._set(returnd)

    def find_indexes(self, times, index):
        start,end = times
        start = datetime.datetime.fromtimestamp(start)
        end = datetime.datetime.fromtimestamp(end)

        diff = abs((end - start).days)
      
        now = datetime.datetime.utcnow() 
        first_date = now - relativedelta(days=diff) 

        search_indexes = []
        if diff > 0:
            for d in range(diff):
                dte = now - relativedelta(days=d)
                datestr = dte.strftime("%Y.%m.%d")
                search_indexes.append("%s-%s" % ( index, datestr ))
        else:   
            search_indexes.append("%s-%s" % ( index, now.strftime("%Y.%m.%d")))

        return search_indexes


    '''
        Formats a relative time str into seconds for you 

        example 1m == 60, 1h == 3600, etc
    '''
    def format_relative_time(self, timestr):
        current_time = bluenote.get_current_utc()

        if 'now' in timestr:
            return current_time

        try:
            m = re.match("^(?P<interval>\-\d+|\d+)(?P<period>\w+)", timestr) 
            if m:
                interval = m.group('interval')
                interval = int(interval.lstrip('-'))
                period = m.group('period')
        except Exception, e:
            logger.exception("unable to parse relative time string: %s" % (e,))
            return

        if 's' in period:
            time_multiplier = 0
        elif 'm' in period:
            time_multiplier = 60
        elif 'h' in period:
            time_multiplier = 3600
        elif 'd' in period:
            time_multiplier = 86400
        elif 'w' in period:
            time_multiplier = 604800
        elif 'M' in period:
            time_multiplier = 18144000
        elif 'Y' in period:
            time_multiplier = 217780000

        diff = int(interval * time_multiplier)

        return current_time - diff


    def make_timeperiod(self, datestr):
        y,m,d = datestr.split('.')
        start = datetime.datetime(int(y),int(m),int(d), 00, 00, 00)
        end = datetime.datetime(int(y),int(m),int(d), 23, 59, 59, 999999)
        start_unix = time.mktime(start.timetuple())
        end_unix = time.mktime(end.timetuple())
        return ( start_unix, end_unix )

    
    def time_index(self,i):
        if "-" in i:
            index_name, date = i.split('-')
            if re.match("\d{1,4}\.\d{1,2}\.\d{1,2}", date):
                period = {i:self.make_timeperiod(date)}
                return period

    
    def get_search_indices(self, time_period, periods):
        if isinstance(time_period, tuple):
            time_period = [ time_period[0], time_period[1] ]
        else:
            time_period = [ time_period ]
        search_indices = []
        for p in periods:
            for i,t in p.iteritems():
                start,end = t
                for tp in time_period:
                    if tp in range(int(start),int(end)):
                        search_indices.append(i)
        return search_indices
