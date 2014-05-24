# appmain.py
# root thing

import os
import json
from flask import Flask

with open('data/test1.json') as f:
    data = json.load(f)

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello world<br/><code>' + str(data) + '</code>'

@app.route('/flerp')
def flerp():
    return 'Flerp.'
