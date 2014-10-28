#!/usr/local/bin/python
import sys
import os
import re
import datetime
import time

from pprint import pprint

BN_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.environ['BN_HOME'] = str(BN_HOME)
sys.path.append(os.path.join(BN_HOME, 'lib'))
# Import our conf path
sys.path.append(os.path.join(BN_HOME, 'etc', 'conf'))
# Import flask app path
sys.path.append(os.path.join(BN_HOME, 'usr', 'share', 'flask'))

from elasticsearch import Elasticsearch
import bluenote
from bluenote.search import Search
from bluenote.search.query import Query
import bluenote.filter
import bluenote.alert
from config import Config
import yaml

# Conf loading
from alerts import alerts
from bn import bncfg 
from bn_mail import mailcfg

from app import app

if __name__ == "__main__":
    app.run()
