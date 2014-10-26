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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from alerts import alerts
from bn_mail import mailcfg

from pprint import pprint

logger = bluenote.get_logger('alert')

def make_email_body(results, ainfo):
    eb = []
    eb.append("<html>")

    eb.append("<head>")
    eb.append("</head>")

    eb.append("<body>")
    eb.append("<p>")
    eb.append("<strong>Severity:</strong> %s <br />" % ainfo.get('severity', ''))
    eb.append("<strong>Alert Name:</strong> %s <br />" % ainfo.get('name', ''))
    eb.append("<strong>Description:</strong> %s <br />" % ainfo.get('description', ''))
    eb.append("<strong>Query:</strong> %s <br />" % ainfo.get('query', ''))
    eb.append("<strong>Trigger Reason:</strong> Because <strong>%s</strong> was <strong>%s</strong> to <strong>%s</strong> <br />" % (ainfo['alert']['counttype'], ainfo['alert']['relation'].upper(), ainfo['alert']['qty']))
    eb.append("<strong>Times:</strong> <b>Start:</b> %s <b>End:</b> %s <br />" % (results['query_intentions']['times']['start_iso'], results['query_intentions']['times']['end_iso']))
    eb.append("</p>")

    eb.append("<strong> Results: </strong>")
    eb.append(bluenote.dict_to_html_table(results.get('_results', '')))
    eb.append("</body>")
    eb.append("</html>")  

    return ''.join(eb)

def find_in_alerts(search_id):
    for al in alerts:
        if search_id in al['name']:
            return al

def email(to, results, alert_name, **kwargs):

    print type(to)
    if not isinstance(to, list):
        to = [to]
    
    print type(to)
    ainfo = find_in_alerts(alert_name)

    sender = kwargs.get('sender', mailcfg['default_sender'])
    subject = kwargs.get('subject', "")

    email_body = make_email_body(results, ainfo)

    msg = MIMEText(email_body, 'html')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ','.join(to)

    try:
        server = smtplib.SMTP(mailcfg['server'])
        server.sendmail(sender, to, msg.as_string())
        server.quit()
    except Exception, e:
        logger.exception("Unable to send email: %s" % e )

    return True

'''
    gets the previous run for an alert
'''
def last_run(es, alert_name):
    res = es.search(index='bluenote-int', doc_type='alert_trigger', q='alert-name:%s' % (alert_name))
    if res:
        for h in res['hits']['hits']:
            return float(h['_source']['time'])
    else:
        return 0
