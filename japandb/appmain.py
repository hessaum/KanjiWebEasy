# appmain.py
# root thing

from flask import Flask, redirect
from japandb import data, templates
import json

app = Flask(__name__)
templates.setup(app)

@app.route('/')
def index():
    return templates.render('index',
        kanji_count=data.get_kanji_count(),
        kanji_total = data.get_kanji_total(),
        word_count=data.get_word_count(),
        word_total = data.get_word_total()
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
    example_sentence_lookup = set();
    for reading, reading_data in word_info['readings'].items():
        reading_kanji_list = []
        for kanji_subword in reading_data['kanji']:
            for kanji in kanji_subword:
                reading_kanji_list.append(kanji)
        kanji_dict[reading] = reading_kanji_list
        for examples in reading_data['examples']:
            # add a tuple of sentenceNum and article
            if 'sentenceNum' in examples:
                example_sentence_lookup.add((examples['sentenceNum'], examples['article']))
    
    #Go through all the example sentences
    all_sentences = list()
    for lookup_info in example_sentence_lookup:
        article_info = data.splice_article_id(lookup_info[1])
        with open('data/in/'+article_info[0]+'/'+article_info[1]+'/'+lookup_info[1]+'.json', encoding='utf-8') as f:
            containing_article = json.load(f)
            current_sentence = 0
            example_sentence = list()
            for token in containing_article['morph']:
            
                #First check if we need to increase sentence number
                if 'word' in token:
                    if current_sentence <= 1 and token['word'] == "<S>":
                        current_sentence += 1
                        continue
                    if token['word'] == '。':
                        current_sentence += 1
                        continue
                
                #Then parse one word
                if current_sentence == lookup_info[0]:
                    if 'ruby' in token:
                        for reading in token['ruby']:
                            if 'r' in reading:
                                example_sentence.append((reading['s'], reading['r']))
                            else:
                                example_sentence.append((reading['s'],))
                if current_sentence > lookup_info[0]:
                    break
                
            all_sentences.append(example_sentence)
                    
    
    return templates.render('word', 
        word=word, 
        info=word_info,
        kanji_dict = kanji_dict,
        kanji_count = data._all_kanji_count,
        word_count = word_usage_info[0],
        word_usage_total = word_usage_info[1],
        kanji_usage_total = data.get_kanji_total(),
        example_sentences = all_sentences
    )
