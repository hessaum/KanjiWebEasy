# data.py
# module responsible for loading & indexing data

import json
from collections import defaultdict

# Perform initialization

with open('data/output.json') as f:
    _categories = json.load(f)

# add "category" to each word, make _words_by_category dict
_words_by_category = {}
_all_words = {}
for category, cat_info in _categories.items():
    _words_by_category[category] = cat_info["words"]
    for word, word_info in cat_info["words"].items():
        word_info["category"] = category
        _all_words[word] = word_info

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
    return sorted(_kanji.keys())

def get_kanji_items():
    return sorted(_kanji.items())

def get_kanji_info_and_words(kanji):
    if not kanji in _kanji:
        return None, None
    return _kanji[kanji], words_by_kanji.get(kanji, [])

def get_word_keys():
    return sorted(_all_words.keys())
    
def get_word_info(word):
    return _all_words.get(word)
