# data.py
# module responsible for loading & indexing data

import json

# Perform initialization

with open('data/test3.json') as f:
    _data = json.load(f)
    
_words = _data["words"]
_kanji = _data["kanji"]

words_by_kanji = {}
for word, word_info in _words.items():
    for kanji in word_info['kanji']:
        words_by_kanji.setdefault(kanji, []).append(word)

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
    return sorted(_words.keys())
    
def get_word_info(word):
    return _words.get(word, None)
