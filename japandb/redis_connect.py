#reddit_connect.py
# -*- coding: utf-8 -*- 

#stdlib
from collections import defaultdict
from operator import itemgetter

#3rd party lib
import redis
import os
import json

#constants
CONST_NUM_AGREES_REQUIRED = 3

local_redis = dict() # local copy of redis database to try and avoid holding connections to the db
unsolved_readings = set() # Approximates which base have readings left. Will never contain less but may contain extra

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
    
    
redis_url = os.getenv('REDISCLOUD_URL', 'redis://localhost:6379')
redis_conn = redis.from_url(redis_url)

# populate resolved files with words it hasn't seen yet 
def populate_database(words, _all_word_count):
    for base, word_info in words['words'].items():
        json_base = redis_conn.get(base)
        if json_base is None:
            resolved_readings = dict()
        else:
            resolved_readings = json.loads(json_base.decode('utf-8'))
        
        has_elements = False
        rewrite_to_database = False
        for reading, reading_info in word_info['readings'].items():
            if len(reading_info['kanji']) == 0:
                continue;
                
            if reading not in resolved_readings:
                resolved_readings[reading] = {}
                
            for i, kanji in enumerate(reading_info['kanji']):
                if len(kanji) == 0:
                    continue
                
                global unsolved_readings
                
                has_elements = True
                furigana = reading_info['furigana'][i]
                if kanji not in resolved_readings[reading]:
                    rewrite_to_database = True
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
        if rewrite_to_database:
            redis_conn.set(base, json.dumps(resolved_readings, ensure_ascii=False))
            
    unsolved_readings = sorted(unsolved_readings, key=lambda x: _all_word_count[x], reverse=True)
            
def build_reading(request):
    i = 0
    readings = []
    while 'kanji_val_'+str(i) in request.form:
        readings.append(request.form['kanji_val_'+str(i)])
        # If user left it blank or somehow the reading the user input wasn't even a possible select
        if readings[i] != 'unsolvable':
            if readings[i] == '' or (readings[i] not in request.form['reading']):
                return None
        i+=1
    return readings
    
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