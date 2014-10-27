# appmain.py
# root thing

from flask import Flask, redirect
from japandb import data, templates
import json

app = Flask(__name__)
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True
templates.setup(app)

@app.route('/')
def index():
    return templates.render('index',
        kanji_count=data.get_kanji_count(),
        kanji_total = data.get_kanji_total(),
        word_count=data.get_word_count(),
        word_total = data.get_word_total()
    )

@app.route('/kanji/')
def show_all_kanji():
    return templates.render('allkanji',
        all_kanji=data.get_kanji_count(),
        kanji_count = data._all_kanji_count,
        kanji_total=data.get_kanji_total()
    )


@app.route('/kanji/<kanji>')
def show_kanji(kanji):
    info = data.get_kanji_info(kanji)
    if not info:
        return redirect('/')
        
    info['words'] = data.sort_word_info(info['words'])
    
    return templates.render('kanji', 
        kanji=kanji, 
        info=info, 
        kanji_count=data._all_kanji_count[kanji],
        kanji_total = data.get_kanji_total(),
        word_count = data._all_word_count,
        usage_total = data.get_kanji_usage_total(kanji)
    )

@app.route('/word/<word>')
def show_word(word):
    word_info = data.get_word_info(word)
    if not word_info:
        return redirect('/')
        
    word_usage_info = data.get_inside_word_usage(word_info)
    word_order = sorted(word_info['readings'].items(), key=lambda x: word_usage_info[0][x[0]], reverse=True)
    
    #Flatten kanji array
    #Also extract article info for example sentence
    kanji_dict = {}
    example_sentence_lookup = {}
    for reading, reading_data in word_info['readings'].items():
        example_sentence_lookup[reading] = set()
        reading_kanji_list = []
        for kanji_subword in reading_data['kanji']:
            for kanji in kanji_subword:
                reading_kanji_list.append(kanji)
        kanji_dict[reading] = reading_kanji_list
        for examples in reading_data['examples']:
            # add a tuple of sentenceNum and article
            if 'sentenceNum' in examples:
                example_sentence_lookup[reading].add((examples['sentenceNum'], examples['article']))
    
    #Go through all the example sentences
    all_sentences = {}
    for key in example_sentence_lookup:
        all_sentences[key] = data.populate_example_sentences(example_sentence_lookup, key)
                
    
    return templates.render('word', 
        word=word, 
        info=word_order,
        class_map = data.class_map,
        kanji_dict = kanji_dict,
        kanji_count = data._all_kanji_count,
        word_count = word_usage_info[0],
        word_usage_total = word_usage_info[1],
        kanji_usage_total = data.get_kanji_total(),
        example_sentences = all_sentences
    )
