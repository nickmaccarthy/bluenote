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
from email.mime.application import MIMEApplication
from email.MIMEBase import MIMEBase
from email import Encoders

from reports import reports
from bn_mail import mailcfg

from pprint import pprint

import requests

logger = bluenote.get_logger('report')

def find_in_reports(search_id):
    for r in reports:
        if search_id in r['name']:
            return r

def make_email_body(rinfo, results=None):
    email_body = requests.post('http://localhost:5000/render/report_email', data={ 
                                                                            'ainfo': json.dumps(rinfo), 
                                                                            'results': json.dumps(results)
                                                                            }
                                ).text
    return email_body

def email(to, report_name, attachment, results=None, **kwargs):
    if not isinstance(to, list):
        to = [to]

    rinfo = find_in_reports(report_name)

    sender = kwargs.get('sender', mailcfg['default_sender'])
    subject = kwargs.get('subject', '')

    email_body = make_email_body(rinfo, results)


    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ','.join(to)
    msgbody = MIMEText(email_body, 'html')
    msg.attach(msgbody)
    
    with open(attachment, 'rb') as fh:
        part = MIMEBase('application', "octet-stream")
        part.set_payload(fh.read())
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="{0}"'.format(os.path.basename(attachment)))
        msg.attach(part)

    try:
        server = smtplib.SMTP(mailcfg['server'])
        server.sendmail(sender, to, msg.as_string())
        server.quit()
    except Exception, e:
        logger.exception("Unable to send email: %s" % e )

    return True
