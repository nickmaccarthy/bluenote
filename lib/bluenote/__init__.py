import sys
import os
import datetime
import calendar
import time
import glob
import imp
import datetime
import socket
import platform
import commands
import logging
import logging.handlers as logging_handler
from autocast import autocast
import random
import re
import collections
import subprocess
import json

from pprint import pprint 

''' returns a unix timestamp of the current time in UTC '''
def get_current_utc():
    return calendar.timegm(datetime.datetime.utcnow().utctimetuple())

''' returns a unix timestamp of the current time localy to host '''
def get_current_time_local():
    return time.time()

''' finds items in a list, can optionally take a list as the needle '''
def find_in_list(needle, lst):
    if isinstance(needle, list):
        for n in needle:
            find_in_list(n, lst)
    else:         
        for l in lst:
            if needle in l:
                return l
            else: 
                continue
        return
    
''' gets a list of confs from a directory '''
def get_confs(PATH):
    confs = []
    for conf in glob.glob("%s/*.conf" % (PATH)):
        confs.append(conf)
    return confs

''' returns back a unix timestamp to a ISO format '''
def epoch2iso(epoch_ts):
    return datetime.datetime.fromtimestamp(float(epoch_ts)).strftime("%Y-%m-%dT%H:%M:%S.%f%Z")


def clean_keys(string): 
    escape_these = ',.\=\n\r\\'
    for char in escape_these:
        string = string.replace(char, '__')
    return string

''' returns a list of dicts into a html table '''
def dict_to_html_table(ourl):
    headers = ourl[0].keys()

    table = []
    theaders = []
    for h in headers:
        theaders.append("<th>%s</th>" % h)

    table.append("<table border='1' cellpadding='1' cellspacing='1'>")
    table.append("<thead>")
    table.append("<tr>")
    for h in headers:
        table.append("<th>%s</th>" % h)
    table.append("</tr>")
    table.append("</thead>")

    table.append("<tbody>")
    tblst = []
    for l in ourl:
        table.append("<tr>")
        for h in headers:
            table.append("<td> %s </td>" % (str(l[h])))
        table.append("</tr>")
    table.append("</tbody>")
    table.append("</table>")

    return ''.join(table)


def datatable(ourl):
    theaders = ourl['_results'][0].keys()

    table = []
    table.append('<table id="datatable" class="table table-striped table-bordered table-hover dataTable no-footer">')
    table.append('<thead>')
    table.append('<tr>')
    for h in theaders:
        table.append("<th>%s</th>" % h)
    table.append("</tr>")
    table.append("</thead>")

    table.append("<tbody>")
    tblst = []
    for l in ourl['_results']:
        print "L: %s" % l
        table.append("<tr>")
        for h in theaders:
            table.append("<td> %s </td>" % (str(l[h])))
        table.append("</tr>")
    table.append("</tbody>")
    table.append("</table>")

    
    htmltable =  ''.join(table)
    return { 'query_intentions': ourl.get('query_intentions'), 'theaders': theaders, 'html': htmltable}    

''' returns a logger instance

    this can be used from other classes/modules like so:

    import bluenote 

    logger = bluenote.get_logger(__name__)
    logger.info("Some log msg")
    logger.error("An error has happened: %s" % (error))
'''
def get_logger(name='bluenote', type='default'):
    import bluenote.log as bnlog

    logger = bnlog.logger()
    logobj = logger.get_logger(name)
    return logobj

''' gets the val for a key in a multi dimensional dict '''
def _get(dct, default, *keys):
    sentry = object()
    def getter(level, key):
        return default if level is sentry else level.get(key, sentry)
    return reduce(getter, keys, dct)


def relative_time_to_seconds(timestr):
    try:
        m = re.match("^(?P<interval>\-\d+|\d+)(?P<period>\w+)", timestr) 
        if m:
            interval = m.group('interval')
            interval = int(interval.lstrip('-'))
            period = m.group('period')
    except Exception, e:
        print "unable to parse relative time string: %s" % e
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

    return interval * time_multiplier


def flatten_dict(d, lkey='', sep='.'):
    ret = {}
    for rkey,val in d.items():
        key = lkey+rkey
        if isinstance(val, dict):
            ret.update(flatten_dict(val, key+sep))
        else:
            ret[key] = val
    return ret


def run_script(script_name, std_in):
    
    script_bins = [ os.path.join(os.environ["BN_HOME"], 'bin', 'scripts') ]

    for bin_dir in script_bins:
        full_path = os.path.join(bin_dir, script_name)

        proc = subprocess.Popen(full_path, stdin=subprocess.PIPE)
        proc.stdin.write(json.dumps(std_in['_results']))

'''
    Loads a python module from a file, and returns it if it has a main() method
'''
def load_module_from_file(filepath, d=None):
    class_inst = None
    expected_class = 'main'

    mod_name, file_ext = os.path.splitext(os.path.split(filepath)[-1])

    if file_ext.lower() == '.py':
         py_mod = imp.load_source(mod_name, filepath)
    elif file_ext.lower() == '.pyc':
         py_mod = imp.load_compiled(mod_name, filepath)

    if hasattr(py_mod, expected_class):
        class_inst = getattr(py_mod, expected_class)(d)

    return class_inst


'''
    Finds a file in a directory
'''
def find_file(name, path):
    if isinstance(path, list):
        for p in path:
            for root, dirc, files in os.walk(p):
                if name in files:
                    return os.path.join(root, name)
    else:
        for root, dirc, files in os.walk(path):
            if name in files:
                return os.path.join(root, name)

''' finds our bin directories '''
def get_bindirs(PATH):
    bindirs = ["%s/bin" % (PATH), "%s/bin/scripts" % (PATH)]
    for dir in glob.glob("%s/*/*/*/bin" % (PATH)):
        bindirs.append(dir)
    return bindirs

''' gets a list of our apps '''
def get_apps(PATH):
    apps = []
    for app in os.listdir(PATH):
        app_info = { "name": app, "path": os.path.join(PATH, app) }
        apps.append(app_info)
    return apps

''' auto casts an input given, returns a casted version '''
@autocast
def castem(e):
    return e


