# appmain.py
# root thing

from flask import Flask, redirect
from japandb import data, templates

app = Flask(__name__)
templates.setup(app)

@app.route('/')
def index():
    return templates.render('index',
        kanji_items=data.get_kanji_items(),
        word_keys=data.get_word_keys()
    )

@app.route('/kanji/<kanji>')
def show_kanji(kanji):
    info, words = data.get_kanji_info_and_words(kanji)
    if not info:
        return redirect('/')
    return templates.render('kanji', kanji=kanji, info=info, words=words)

@app.route('/word/<word>')
def show_word(word):
    word_info = data.get_word_info(word)
    if not word_info:
        return redirect('/')
    return templates.render('word', word=word, info=word_info)
