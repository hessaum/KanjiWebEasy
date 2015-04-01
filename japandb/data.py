# data.py
# -*- coding: utf-8 -*- 
# module responsible for loading & indexing data

# stdlib
import json
import os
import gzip
from operator import itemgetter
from collections import defaultdict

# 3rd party lib
import jsonpickle

# user defined
from japandb import wordutils, tree, redis_connect

# constants
CONST_WORDS_PER_PAGE = 1000
CONST_WORD_SENTENCE_LIMIT = 10
CONST_TO_TRIM = '　 ' # Japanese whitespace and ASCII whitespace
    
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
                
    if wordutils.is_valid(word, _all_words[word]):
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

#reading solving loadin
redis_connect.populate_database(words, _all_word_count)

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
    
def get_valid_word_total():
    return _valid_word_total;

def get_valid_word_count():
    return sorted(_valid_word_count.items(), key=itemgetter(1, 0), reverse=True)

def sort_word_info(word_array):
    return sorted(word_array, key=lambda x: (_all_word_count[x],x), reverse=True)
    
def sort_kanji_info(word_array):
    return sorted(word_array, key=lambda x: (_all_kanji_count[x],x), reverse=True)

def splice_article_id(articleId):
    if articleId.startswith('news'):
        articleId = articleId[4:]
    time = articleId[0:8];
    id = articleId[9:];
    return (time, id)

def get_inside_word_usage(word_info):
    count_total = 0
    count_map = {}
    for reading, reading_info in word_info['readings'].items():
        num_examples = 0
        for example in reading_info['examples']:
            num_examples += len(reading_info['examples'][example])
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
    for i in range(len(word)):
        if wordutils.is_digit(word[i]):
            word = word[0:i] + wordutils.convert_numeral(word[i]) + word[i+1:]
            
    # represents an overestimate of all the words that match
    max_word_set = set()
    for char in word:
        if wordutils.is_kanji(char):
            kanji_info = get_kanji_info(char)
            if kanji_info == None:
                return []
            if(len(max_word_set) == 0):
                max_word_set = set(kanji_info['words'])
            else:
                max_word_set &= set(kanji_info['words'])
        else:
            letter_map = _letter_map[char]
            if letter_map == None:
                return []
            if(len(max_word_set) == 0):
                max_word_set |= letter_map
            else:
                max_word_set &= letter_map
        
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
        while(i < len(word) and wordutils.is_kanji(word[i])):
            i += 1
        if start_index != i:
            kanji_list.append(word[start_index:i])
        
        start_index = i
        while(i < len(word) and not wordutils.is_kanji(word[i])):
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

def populate_example_sentences(lookup_info, sentence_limit, word_info=None):
    sentences = []
    for lookup_info in lookup_info:
        if lookup_info[1].startswith('news'):
            filename = lookup_info[1]
        else:
            filename = 'news'+lookup_info[1]
        article_info = splice_article_id(lookup_info[1])
        with open('data/in/'+article_info[0]+'/'+article_info[1]+'/'+filename+'.json', encoding='utf-8') as f:
            containing_article = json.load(f)
            current_sentence = 0
            example_sentence = []
            
            # If we're trying to find the first sentence AKA the title
            if lookup_info[0] == 1:
                example_sentence.append(('(タイトル） ',))
            in_quote = False
            for token in containing_article['morph']:
                if current_sentence > lookup_info[0]:
                    break
                    
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
                        # we want a trailing dot at the end
                        if current_sentence == lookup_info[0]:
                            example_sentence.append('。')
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
            
            if word_info != None:
                insert_bold(example_sentence, word_info)
            
            sentences.append(example_sentence)
            
            if len(sentences) == sentence_limit:
                break
    return sentences

tree = tree.GST()
CONST_REWRITE_GZIPS = False

if CONST_REWRITE_GZIPS:
    for (root, dirs, files) in os.walk('data/in/'):
        if len(dirs) == 0:
            for file in files:
                with open(os.path.join(root,file), encoding='utf-8') as f:
                    article = json.load(f)['text']
                    title_index = article.find(' ')
                    article = article[0:title_index] + '。' + article[title_index:]
                    article = article.replace(' ', '')
                    
                    last_cut = 0
                    in_quote = False
                    sentence_count = 1
                    for i in range(len(article)):
                        if article[i] == '「':
                            in_quote = True
                        if article[i] == '」':
                            in_quote = False
                        if not in_quote and article[i] == '。':
                            tree.add(article[last_cut:i].strip(CONST_TO_TRIM), (sentence_count, file[4:len(file)-5]))
                            last_cut = i+1
                            sentence_count += 1
                    if last_cut != len(article):
                        tree.add(article[last_cut:i].strip(CONST_TO_TRIM), (sentence_count, file[4:len(file)-5]))  
    for child in tree.root.cld:
        with gzip.open('data/sentences/'+str(ord(child.cts[:1]))+'.gz', 'wb') as f:
            f.write(bytes(jsonpickle.encode(child), 'UTF-8'))

def load_key(key):
    folder_key = ord(key[:1])
    
    for child in tree.root.cld:
        if ord(child.cts[:1]) == folder_key:
            return True
    
    path = 'data/sentences/'+str(folder_key)+'.gz'
    if not os.path.exists(path):
        return False
    
    with gzip.open(path, 'r') as f:
        tree.root.cld.append(jsonpickle.decode(f.read().decode('UTF-8')))
        return True
        
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