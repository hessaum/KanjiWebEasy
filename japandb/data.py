# data.py
# module responsible for loading & indexing data

import json
import os
import redis
from collections import defaultdict
from operator import itemgetter

# constants
CONST_NUM_AGREES_REQUIRED = 3
CONST_WORDS_PER_PAGE = 1000

#reading utils

def contains_num(word):
    return any(c.isdigit() for c in word)
    
def is_latin(c):
    char = ord(c)
    return (char > 0xFF00) and (char < 0xFFA0)
    
def is_kanji(c):
    char = ord(c)
    return (char > 0x4E00) and (char < 0x9FAF)

def is_hiragana(c):
    char = ord(c)
    return (char > 0x3041) and (char < 0x3094)
    
def is_katakana(c):
    char = ord(c)
    return (char > 0x30A1) and (char < 0x30FA)
    
def is_japanese(word):
    #if it contains at least one hiragana/katakana/kanji
    for c in word:
        if is_kanji(c) or is_hiragana(c) or is_katakana(c):
            return True
    return False

def contains_non_grammatical(word):
    for reading, reading_info in _all_words[word]['readings'].items():
        if reading_info['class'] is not 'B':
            return True
    return False

def is_valid(word):
    return is_japanese(word) and contains_non_grammatical(word)
    
def is_solved(kanji_index, solv_info):
    if len(solv_info['split']) == 0:
        return None
        
    given_reading = defaultdict(int)
    for j in range(len(solv_info['split'])):
        given_reading[solv_info['split'][j][kanji_index]] += 1
    popular_reading = sorted(given_reading.items(), key=itemgetter(1), reverse=True)[0]
    if popular_reading[1] >= CONST_NUM_AGREES_REQUIRED:
        return popular_reading[0]
    else:
        return None
        
def has_unsolved(kanji, solv_info):
    for i in range(len(kanji)):
        if is_solved(i, solv_info) is None:
            return True
    return False
    
# Perform initialization

with open('data/output.json', encoding='utf-8') as f:
    words = json.load(f)

_all_words = {}
_all_word_count = {}
_valid_word_count = {}
_all_kanji_count = {}
_letter_map = defaultdict(set)

def count_examples(examples):
    example_count = 0
    for article, sentences in examples.items():
        example_count = example_count + len(sentences)
    return example_count
        
for word, word_info in words['words'].items():
    _all_words[word] = word_info
    word_occurrence = 0
    for reading, reading_info in word_info['readings'].items():
        for furi in reading:
            _letter_map[furi].add(word)
        example_count = count_examples(reading_info['examples'])
        word_occurrence = word_occurrence + example_count
        
        for kanji_str in reading_info['kanji']:
            for kanji in kanji_str:
                _all_kanji_count[kanji] = _all_kanji_count.get(kanji, 0) + example_count
                
    if is_valid(word):
        _valid_word_count[word] = word_occurrence
    _all_word_count[word] = word_occurrence

_kanji_total = sum(count for kanji, count in _all_kanji_count.items())
_word_total = sum(count for word, count in _all_word_count.items())
_valid_word_total = sum(count for word, count in _valid_word_count.items())

# index the kanji in the words
def _make_kanji_default():
    return {'words': set()}
_kanji = defaultdict(_make_kanji_default)

for word, word_info in _all_words.items():
    for reading, reading_info in word_info["readings"].items():
        for kanji_str in reading_info["kanji"]:
            for kanji in kanji_str:
                _kanji[kanji]['words'].add(word)

#reading solving loading
redis_url = os.getenv('REDISCLOUD_URL', 'redis://localhost:6379')
redis_conn = redis.from_url(redis_url)
local_redis = dict() # local copy of redis database to try and avoid holding connections to the db
unsolved_readings = set() # Approximates which base have readings left. Will never contain less but may contain extra

# populate resolved files with words it hasn't seen yet    
def populate_database():
    for base, word_info in words['words'].items():
        json_base = redis_conn.get(base)
        if json_base is None:
            resolved_readings = dict()
        else:
            resolved_readings = json.loads(json_base.decode('utf-8'))
        
        has_elements = False
        for reading, reading_info in word_info['readings'].items():
            if len(reading_info['kanji']) == 0:
                continue;
                
            if reading not in resolved_readings:
                resolved_readings[reading] = {}
                
            for i, kanji in enumerate(reading_info['kanji']):
                if len(kanji) == 0:
                    continue
                
                has_elements = True
                furigana = reading_info['furigana'][i]
                if kanji not in resolved_readings[reading]:
                    if len(kanji) == 1 or kanji == furigana:
                        resolved_readings[reading][kanji] = {'furi': reading_info['furigana'][i]}
                    else:
                        resolved_readings[reading][kanji] = {'split' : [], 'ip': [], 'furi': furigana}
                        unsolved_readings.add(base)
                else:
                    if 'ip' not in resolved_readings[reading][kanji]:
                        continue
                    if has_unsolved(kanji, resolved_readings[reading][kanji]):
                        unsolved_readings.add(base)
        
        if has_elements:
            local_redis[base] = resolved_readings
            redis_conn.set(base, json.dumps(resolved_readings, ensure_ascii=False))
    
populate_database()
# Public interface
unsolved_readings = sorted(unsolved_readings, key=lambda x: _all_word_count[x], reverse=True)

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
    
def get_valid_word_total():
    return _valid_word_total;

def get_valid_word_count():
    return sorted(_valid_word_count.items(), key=itemgetter(1, 0), reverse=True)

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

def contains_ascending(text, token_list):
    start_pos = 0
    for token in token_list:
        index = text.find(token, start_pos)
        if index == -1:
            return False
        start_pos += index + len(token)
    
    return True
            
def search(word):
    # represents an overestimate of all the words that match
    max_word_set = set()
    for char in word:
        if is_kanji(char):
            if(len(max_word_set) == 0):
                max_word_set = set(get_kanji_info(char)['words'])
            else:
                max_word_set &= set(get_kanji_info(char)['words'])
        else:
            if(len(max_word_set) == 0):
                max_word_set |= _letter_map[char]
            else:
                max_word_set &= _letter_map[char]
        
        # if we ever have no elements left, we can just stop
        if(len(max_word_set) == 0):
            return []
    
    # need to filter our max set to find words that contain both
    # 1) the kanji list in ascending order
    # 2) the furigana list in ascending order
    kanji_list = []
    furi_list = []
    i = 0
    while(i < len(word)):
        start_index = i
        while(i < len(word) and is_kanji(word[i])):
            i += 1
        if start_index != i:
            kanji_list.append(word[start_index:i])
        
        start_index = i
        while(i < len(word) and not is_kanji(word[i])):
            i += 1
        if start_index != i:
            furi_list.append(word[start_index:i])
    
    # create an approximate set. It removes words from the max word set that didn't have ascending order for tokens
    # this set is an approximate because the presence/lack of kanji can cause issues
    approx_set = set()
    for word in max_word_set:
        does_match = False
        word_info = _all_words[word]['readings']
        for reading in word_info: 
            if does_match:
                break
            if contains_ascending(reading, furi_list):
                # flatten kanji in the word
                kanji_text = ''
                for kanji in word_info[reading]['kanji']:
                    kanji_text += kanji
                
                if contains_ascending(kanji_text, kanji_list):
                    approx_set.add((word, _all_word_count[word]))
                    does_match = True
            
    return sorted(approx_set, key=itemgetter(1, 0), reverse=True)
    
def get_running_total(sorted_list):
    running_count = []
    previous_count = 0
    for i, kanji in enumerate(sorted_list):
        running_count.append(previous_count + kanji[1]);
        previous_count = previous_count + kanji[1]
    
    return running_count
    
def insert_bold(example_sentence, word_info):
    insertion_points = []
    
    for i in range(len(example_sentence)):
        for j in range(len(word_info['furigana'])):
            if word_info['kanji'][j] == '':
                if example_sentence[i+j][0] != word_info['furigana'][j]:
                    break
            else:
                if example_sentence[i+j][0] != word_info['kanji'][j]:
                    break
            
            if j == len(word_info['furigana'])-1:
                insertion_points.append(i)
    
    for i, point in enumerate(insertion_points):
        example_sentence.insert(point, ('<b>',))
        example_sentence.insert(point+len(word_info['furigana'])+1, ('</b>',))
        for j in range(i+1, len(insertion_points)):
            insertion_points[j] += 2

def populate_example_sentences(lookup_info, word_info):
    sentences = []
    for lookup_info in lookup_info:
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
            
            insert_bold(example_sentence, word_info)
            
            sentences.append(example_sentence)
            
            if len(sentences) == 10:
                break
    return sentences

def handle_reading_post(request):
    base = request.form['base']
    reading = request.form['reading']
    kanji = request.form['kanji']
    kanji_readings = build_reading(request)
    
    json_base = redis_conn.get(base);
    # throw away impossible input
    if json_base is None:
        return
    else:
        resolved_readings = json.loads(json_base.decode('utf-8'))
    if kanji_readings is None:
        return
    if not reading in resolved_readings:
        return
    if not kanji in resolved_readings[reading]:
        return
    # don't allow the same IP twice
    if not request.remote_addr in resolved_readings[reading][kanji]['ip']:
        resolved_readings[reading][kanji]['split'].append(kanji_readings)
        if not request.headers.getlist("X-Forwarded-For"):
           ip = request.remote_addr
        else:
           ip = request.headers.getlist("X-Forwarded-For")[0]
        resolved_readings[reading][kanji]['ip'].append(ip)
        local_redis[base] = resolved_readings
        redis_conn.set(base, json.dumps(resolved_readings, ensure_ascii=False))

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