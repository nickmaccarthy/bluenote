#!/usr/local/bin/python
import sys
import os
import json

print "Query killer is alive!"
in_json = sys.stdin.read()

try:
    results = json.loads(in_json)
except Exception, e:
    print("Unable to decode json input. Reason: %s" % (e))


for r in results:
    print " I would now kill process: %s on host:%s because query_time is %s" % (r['_source.plist.Id'], r['_source.host'], r['_source.plist.Time'])

