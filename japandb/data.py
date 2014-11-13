# data.py
# module responsible for loading & indexing data

import json
import os
import redis
from collections import defaultdict
from operator import itemgetter

# Perform initialization

with open('data/output.json', encoding='utf-8') as f:
    words = json.load(f)

_all_words = {}
_all_word_count = {}
_all_kanji_count = {}

for word, word_info in words['words'].items():
    _all_words[word] = word_info
    word_occurrence = 0
    for reading, reading_info in word_info['readings'].items():
        example_count = 0
        for article, sentences in reading_info['examples'].items():
            example_count = example_count + len(sentences)
        word_occurrence = word_occurrence + example_count
        
        for kanji_str in reading_info['kanji']:
            for kanji in kanji_str:
                _all_kanji_count[kanji] = _all_kanji_count.get(kanji, 0) + example_count
    _all_word_count[word] = word_occurrence

_kanji_total = sum(count for kanji, count in _all_kanji_count.items())
_word_total = sum(count for word, count in _all_word_count.items())
    
# index the kanji in the words
def _make_kanji_default():
    return {'words': set(), 'readings': {}}
_kanji = defaultdict(_make_kanji_default)

for word, word_info in _all_words.items():
    for reading, reading_info in word_info["readings"].items():
        for kanji_str in reading_info["kanji"]:
            for kanji in kanji_str:
                _kanji[kanji]['words'].add(word)

#reading solving loading
redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
redis_conn = redis.from_url(redis_url)
def load_redis_json(redis_conn):
    if redis_conn.exists('json'):
        return json.loads(redis_conn.get('json').decode('utf-8'))
    else:
        return {}

resolved_readings = load_redis_json(redis_conn)
# populate resolved files with words it hasn't seen yet    
def populate_database():
    for base, word_info in words['words'].items():
        for reading, reading_info in word_info['readings'].items():
            if len(reading_info['kanji']) == 0:
                continue;
            for i, kanji in enumerate(reading_info['kanji']):
                if len(kanji) == 0:
                    continue
                if not base in resolved_readings:
                    resolved_readings[base] = {}
                if not reading in resolved_readings[base]:
                    resolved_readings[base][reading] = {}
                if not kanji in resolved_readings[base][reading]:
                    resolved_readings[base][reading][kanji] = {'split' : [], 'ip': [], 'furi': reading_info['furigana'][i]}
                if len(kanji) == 1:
                    if 'ip' in resolved_readings[base][reading][kanji]:
                        del resolved_readings[base][reading][kanji]['ip']
                        del resolved_readings[base][reading][kanji]['split']

    redis_conn.set('json', json.dumps(resolved_readings, ensure_ascii=False))
    
populate_database()
# Public interface

def get_kanji_keys():
    return sorted(_kanji.keys(), key=_all_kanji_count.get, reverse=True)

def get_kanji_sorted_by_count():
    return sorted(_all_kanji_count.items(), key=itemgetter(1, 0), reverse=True)
    
def get_kanji_items():
    return sorted(_kanji.items())

def get_kanji_info(kanji):
    return _kanji.get(kanji)
    
def get_kanji_total():
    return _kanji_total

def get_word_keys():
    return sorted(_all_words.keys(), key=_all_word_count.get, reverse=True)
    
def get_word_info(word):
    return _all_words.get(word)
    
def get_word_total():
    return _word_total;

def get_word_count():
    return sorted(_all_word_count.items(), key=itemgetter(1, 0), reverse=True)

def sort_word_info(word_array):
    return sorted(word_array, key=lambda x: (_all_word_count[x],x), reverse=True)
    
def sort_kanji_info(word_array):
    return sorted(word_array, key=lambda x: (_all_kanji_count[x],x), reverse=True)

def splice_article_id(articleId):
    time = articleId[4:12];
    id = articleId[13:];
    return (time, id)

def get_inside_word_usage(word_info):
    count_total = 0
    count_map = {}
    for reading, reading_info in word_info['readings'].items():
        num_examples = len(reading_info['examples'])
        count_total += num_examples
        count_map[reading] = num_examples
        
    return (count_map, count_total)

def get_kanji_usage_total(kanji):
    count_total = 0
    for word in _kanji[kanji]['words']:
        count_total += _all_word_count[word]
    return count_total
    
def get_running_total(sorted_list):
    running_count = []
    previous_count = 0
    for i, kanji in enumerate(sorted_list):
        running_count.append(previous_count + kanji[1]);
        previous_count = previous_count + kanji[1]
    
    return running_count
    
def populate_example_sentences(example_sentence_lookup, key):
    sentences = []
    for lookup_info in example_sentence_lookup[key]:
        article_info = splice_article_id(lookup_info[1])
        with open('data/in/'+article_info[0]+'/'+article_info[1]+'/'+lookup_info[1]+'.json', encoding='utf-8') as f:
            containing_article = json.load(f)
            current_sentence = 0
            example_sentence = []
            in_quote = False
            for token in containing_article['morph']:
            
                #First check if we need to increase sentence number
                if 'word' in token:
                    if current_sentence <= 1 and token['word'] == "<S>":
                        current_sentence += 1
                        continue
                        
                    if token['word'] == '「':
                        in_quote = True
                        
                    if token['word'] == '」':
                        in_quote = False
                    
                    if token['word'] == '。' and in_quote == False:
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
            sentences.append(example_sentence)
            
            if len(sentences) == 10:
                break
    return sentences

def handle_reading_post(request):
    base = request.form['base']
    reading = request.form['reading']
    kanji = request.form['kanji']
    kanji_readings = build_reading(request)
    # throw away impossible input
    if kanji_readings is None:
        return
    if not base in resolved_readings:
        return
    if not reading in resolved_readings[base]:
        return
    if not kanji in resolved_readings[base][reading]:
        return
    # don't allow the same IP twice
    if not request.remote_addr in resolved_readings[base][reading][kanji]['ip']:
        resolved_readings[base][reading][kanji]['split'].append(kanji_readings)
        resolved_readings[base][reading][kanji]['ip'].append(request.environ['REMOTE_ADDR'])
        redis_conn.set('json', json.dumps(resolved_readings, ensure_ascii=False))

def build_reading(request):
    i = 0
    readings = []
    while 'kanji_val_'+str(i) in request.form:
        readings.append(request.form['kanji_val_'+str(i)])
        # If user left it blank or somehow the reading the user input wasn't even a possible select
        if readings[i] == '' or not (readings[i] in request.form['reading']):
            return None
        i+=1
    return readings
    
class_map = {
	"0" : "Regular word",
	"1" : "Regular word",
	"2" : "Regular word",
	"3" : "Regular word",
	"4" : "Regular word",
	"L" : "Location",
	"B" : "Grammatical",
	"F" : "Foreign influence",
	"C" : "Group name",
	"N" : "Name",
	'-' : ""
}