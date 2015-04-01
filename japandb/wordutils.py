#wordutils.py
# -*- coding: utf-8 -*- 

def contains_num(word):
    return any(c.isdigit() for c in word)
    
def is_latin(c):
    char = ord(c)
    return (char > 0xFF00) and (char < 0xFFA0)
    
def is_kanji(c):
    char = ord(c)
    return (char >= 0x4E00) and (char <= 0x9FAF)

def is_hiragana(c):
    char = ord(c)
    return (char >= 0x3041) and (char <= 0x3094)
    
def is_katakana(c):
    char = ord(c)
    return (char >= 0x30A1) and (char <= 0x30FA)
    
def kata_to_hira(word):
    new_word = ''
    for c in word:
        if is_katakana(c):
            new_word += chr(ord(c) - 0x30A1 + 0x3041)
        else:
            new_word += c
            
    return new_word
    
def convert_numeral(c):
    # 0x30 is the 0 in roman numberals
    # 0xFF10 is the 0 in halfwidth/fullwidth
    return chr((ord(c)-0x30)+0xFF10)

def is_digit(c):
    char = ord(c)
    return (char >= 0x30) and (char <= 0x39)
    
def is_japanese(word):
    #if it contains at least one hiragana/katakana/kanji
    for c in word:
        if is_kanji(c) or is_hiragana(c) or is_katakana(c):
            return True
    return False

# Precondition: word_info should be have a ['readings'] property
def contains_non_grammatical(word_info):
    for reading, reading_info in word_info['readings'].items():
        if reading_info['class'] is not 'B':
            return True
    return False

def is_valid(word, word_info):
    return is_japanese(word) and contains_non_grammatical(word_info)