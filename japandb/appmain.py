# appmain.py
# root thing

import os
import json
from flask import Flask, render_template

with open('data/test2.json') as f:
    data = json.load(f)

app = Flask(__name__)

@app.route('/')
def hello():
    return render_template('index.html', data=data)

@app.route('/flerp')
def flerp():
    return 'Flerp.'
