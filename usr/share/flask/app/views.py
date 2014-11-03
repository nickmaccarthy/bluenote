from functools import wraps
from flask import render_template, request, url_for, flash, redirect, jsonify, session, Response
from app import app
import json

from bluenote.search import Search
import bluenote.filter
from bluenote import datatable, flatten_dict

s = Search()

@app.route('/')
def index():
    return render_template('search.html')

@app.route('/search/bnquery', methods=['POST'])
def bnsearch():
    if request.method == 'POST':
        bnsearch = request.form.get('bnsearch')
        results = s.query(bnsearch, _from="-10m", _to="now")
        return render_template('bn_search.html', query=bnsearch, results=datatable(bluenote.filter.result_set(results)))

@app.route('/render/email', methods=['POST'])
def render_email():
    if request.method == 'POST':
        ainfo = json.loads(request.form.get('ainfo'))
        results = json.loads(request.form.get('results'))
        results_table = request.form.get('results_table')
        return render_template('email.html', ainfo=ainfo, results=results, results_table=results_table )



