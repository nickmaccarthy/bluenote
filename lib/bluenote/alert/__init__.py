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

import requests

logger = bluenote.get_logger('alert')

def make_email_body(results, ainfo):
    try:
        email_body = requests.post('http://localhost:5000/render/email', data={
                                                                            'ainfo': json.dumps(ainfo), 
                                                                            'results': json.dumps(results), 
                                                                            'results_table': bluenote.dict_to_html_table(results.get('_results', '')) 
                                                                        }
                                    ).text
        return email_body
    except Exception, e:
        log_msg = "Unable to make request to render email template: %s" % e
        logger.exception(log_msg)

def find_in_alerts(search_id):
    for al in alerts:
        if search_id in al['name']:
            return al

def email(to, results, alert_name, **kwargs):

    if not isinstance(to, list):
        to = [to]
    
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
