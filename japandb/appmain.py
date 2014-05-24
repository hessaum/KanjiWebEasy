# appmain.py
# root thing

import os
import json
from flask import Flask, render_template, redirect

with open('data/test3.json') as f:
    data = json.load(f)

app = Flask(__name__)

@app.context_processor
def inject_python():
    return dict(len=len)

@app.route('/')
def hello():
    kanji_info = sorted(data['kanji'].items())
    word_keys = sorted(data['words'].keys())
    return render_template('index.html', kanji_items=kanji_info, word_keys=word_keys)

@app.route('/kanji/<kanji>')
def show_kanji(kanji):
    if kanji not in data['kanji']:
        return redirect('/')
    
    kanji_info = data['kanji'][kanji]
    return render_template('kanji.html', kanji=kanji, info=kanji_info)

@app.route('/word/<word>')
def show_word(word):
    if word not in data['words']:
        return redirect('/')
    
    word_info = data['words'][word]
    return render_template('word.html', word=word, info=word_info)

@app.route('/flerp')
def flerp():
    return 'Flerp.'
