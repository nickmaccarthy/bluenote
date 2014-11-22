#!/usr/local/bin/python2.7
import sys
import os
import json
import datetime
import time
import pprint


BN_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
os.environ['BN_HOME'] = str(BN_HOME)

activate_this = os.path.join(BN_HOME, 'env', 'bin', 'activate_this.py')
execfile(activate_this, dict(__file__=activate_this))

sys.path.append(os.path.join(BN_HOME, 'lib'))
# Import our conf path
sys.path.append(os.path.join(BN_HOME, 'etc', 'conf'))

import bluenote
import bluenote.alert

from fabric.api import *
from fabric.colors import green, red
from fabric.contrib import *

env.user = 'nmaccarthy'
env.password = 'n1ckr0ck5!'

class FabricSupport:
    def __init__ (self):
        pass

    def run(self, host, port, command):
        env.host_string = "%s:%s" % (host, port)
        env.warn_only = True
        return run(command)

    def sudo(self, host, port, command):
        env.host_string = "%s:%s" % (host, port)
        env.warn_only = True
        with hide('running', 'stdout', 'stderr'):
            return sudo(command)

def log_it(msg, host, kwargs):

    ## set our log time
    log_time = time.strftime("%Y-%m-%d %H:%M:%S %Z")

    log = []
    log.append('%s [%s] -' % (log_time, host))
    log.append('MSG: %s' % (msg))

    kvs = []
    for k,v in kwargs.iteritems():
        kvs.append('%s = %s' %  (k, v))
    kvs = ', '.join(kvs)
    log.append(kvs)

    flat = ' '.join(log)
    flat = flat+"\n"

    with open(os.path.join(BN_HOME, 'var', 'log', 'query-killer-%s.log' % (time.strftime('%Y.%m.%d'))), 'a') as f:
        f.write(flat)

F = FabricSupport()

logger = bluenote.get_logger('query-killer-script')

logger.info("Query killer is alive!")
in_json = sys.stdin.read()

try:
    results = json.loads(in_json)
except Exception, e:
    print("Unable to decode json input. Reason: %s" % (e))


for r in results:
    host = r['_source.host']
    port = 22
    logger.info(" I would now kill process: %s on host:%s because query_time is %s" % (r['_source.plist.Id'], r['_source.host'], r['_source.plist.Time']))

    try:
        kill_the_query = F.sudo(host, port, 'mysql -e "kill %s"' % r['_source.plist.Id']) 
        logmsg = "The Query Killer on %s has killed process: %s on host: %s because the query_time is %s seconds.<br /><br />Query: %s<br />State: %s" % (bluenote.get_hostname(), r['_source.plist.Id'], r['_source.host'], r['_source.plist.Time'], r['_source.plist.Info'], r['_source.plist.State'], ) 
        log_it("Query Auto Killed", host, r)
        email_subject = 'Bluenote Query Killer: Auto Killed Query'
        email_it = bluenote.alert.email_basic(['nmaccarthy@shapeup.com', 'devops@shapeup.com'], email_subject, logmsg) 
    except Exception, e:
        logger.exception("Unable to kill query: %s , result_details: %s" % (e,r))

