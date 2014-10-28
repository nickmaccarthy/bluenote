from functools import wraps
from flask import render_template, request, url_for, flash, redirect, jsonify, session, Response
from app import app
import json

@app.route('/render/email', methods=['POST'])
def index():
    if request.method == 'POST':
        ainfo = json.loads(request.form.get('ainfo'))
        results = json.loads(request.form.get('results'))
        results_table = request.form.get('results_table')
        return render_template('email.html', ainfo=ainfo, results=results, results_table=results_table )
