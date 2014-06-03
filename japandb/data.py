# data.py
# module responsible for loading & indexing data

import json
from collections import defaultdict
from operator import itemgetter

# Perform initialization

with open('data/output.json', encoding='utf-8') as f:
    _categories = json.load(f)

# add "category" to each word, make _words_by_category dict
_words_by_category = {}
_all_words = {}
_all_word_count = {}
_all_kanji_count = {}

for category, cat_info in _categories.items():
    _words_by_category[category] = cat_info["words"]
    for word, word_info in cat_info["words"].items():
        word_info["category"] = category
        _all_words[word] = word_info
        word_occurrence = 0
        for reading, reading_info in word_info["readings"].items():
            example_count = len(reading_info["examples"])
            word_occurrence = word_occurrence + example_count
            
            for kanji_str in word_info["kanji"]:
                for kanji in kanji_str:
                    _all_kanji_count[kanji] = _all_kanji_count.get(kanji, 0) + example_count
        _all_word_count[word] = word_occurrence

_kanji_total = sum(count for kanji, count in _all_kanji_count.items())
_word_total = sum(count for word, count in _all_word_count.items())
    
# index the kanji in the words
def _make_kanji_default():
    return {'words': [], 'readings': {}}
_kanji = defaultdict(_make_kanji_default)

for word, word_info in _all_words.items():
    for kanji_str in word_info["kanji"]:
        for kanji in kanji_str:
            _kanji[kanji]['words'].append(word)
    # todo: determine readings properly

# Public interface

def get_kanji_keys():
    return sorted(_kanji.keys(), key=_all_kanji_count.get, reverse=True)

def get_kanji_count():
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