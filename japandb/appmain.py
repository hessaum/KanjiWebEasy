# appmain.py
# -*- coding: utf-8 -*- 

from flask import Flask, redirect, request, g, session, flash, send_from_directory
from japandb import data, tree, templates
from collections import defaultdict
from operator import itemgetter
from os import path
from flask.ext.openid import OpenID
from openid.extensions import pape
import json
import hashlib
import math

app = Flask(__name__)
app.config.update(SECRET_KEY = 'n8@`K$qo6VG.>)=E!,x]S5U.F8O345')
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

templates.setup(app)

# setup flask-openid
oid = OpenID(app, safe_roots=[], extension_responses=[pape.Response])

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')
      
@app.route('/apple-touch-icon.png')
def apple_touch():
    return send_from_directory(path.join(app.root_path, 'static'), 'apple-touch-icon.png')
   
   
@app.errorhandler(404)
def page_not_found(error):
    return templates.render('page_not_found'), 404
    
@app.route('/')
def index():
    return templates.render('index')

@app.route('/plerp/', methods=['GET', 'POST'])
def dump_database():
    if request.method == 'POST':
        password = hashlib.sha1(request.form['password'].encode('utf-8')).hexdigest()
        if  password == '4ae4a6888caa20abe362f9a2b4569dc1c166cc2e':
            data.redis_conn.flushdb()
            data.local_redis = {}
            data.populate_database()
            return templates.render('dump_database', delete=True)  
        elif password == '277c17bf478687ba2b53a8929e945d4f33078384':
            return templates.render('dump_database', database=data.redis_conn, keys=data.redis_conn.keys('*'))
        elif password == '0d366a470b59ab03e98cea9bffe85e208ada3406':
            return templates.render('dump_database', left=data.unsolved_readings)
        
    return templates.render('dump_database')

@app.route('/readingsolver/', methods=['GET', 'POST'])
def reading_solver():
    if request.method == 'POST':
        data.handle_reading_post(request)
    
    for base in data.unsolved_readings:
        word_info = json.loads(data.redis_conn.get(base).decode('utf-8'))
        for reading, reading_info in word_info.items():
            for subword, subword_info in reading_info.items():
                if 'ip' not in subword_info:
                    continue
                
                if not data.has_unsolved(subword, subword_info):
                    continue
                    
                if not request.headers.getlist("X-Forwarded-For"):
                   ip = request.remote_addr
                else:
                   ip = request.headers.getlist("X-Forwarded-For")[0]
                if ip in subword_info['ip']:
                    continue
                
                return templates.render('readingsolver', base=base, reading=reading, furigana=subword_info['furi'], kanji=subword)
            
    return templates.render('readingsolver')

@app.route('/kanji/')
def show_all_kanji():
    sorted_kanji = [c for c in data.get_kanji_sorted_by_count() if (not data.is_latin(c[0]))]
    return templates.render('allkanji',
        all_kanji=sorted_kanji,
        kanji_count = data._all_kanji_count,
        running_total = data.get_running_total(sorted_kanji),
        kanji_total=data.get_kanji_total()
    )


@app.route('/kanji/<kanji>')
def show_kanji(kanji):
    info = data.get_kanji_info(kanji)
    if not info:
        return redirect('/')
        
    info['words'] = data.sort_word_info(info['words'])
    
    reading_map = defaultdict(int)
    reading_count = 0
    
    word_count = data._all_word_count
    for word in info['words']:
        solved_reading = data.local_redis[word]
        for reading, reading_info in solved_reading.items():
            count = data.count_examples(data.words['words'][word]['readings'][reading]['examples'])
            for solv_word, solv_info in reading_info.items():
                for i in range(len(solv_word)):
                    if solv_word[i] == kanji:
                        if 'ip' not in solv_info:
                            if not data.contains_num(solv_info['furi']):
                                hira_reading = data.kata_to_hira(solv_info['furi'])
                                reading_map[hira_reading] += count
                            else:
                                reading_map['Unknown'] += count
                        else: 
                            popular_reading = data.is_solved(i, solv_info)
                            if popular_reading is not None:
                                if popular_reading != 'unsolvable':
                                    popular_reading = data.kata_to_hira(popular_reading)
                                    reading_map[popular_reading] += count
                            else:
                                reading_map['Unknown'] += count
                        reading_count += count
    
    reading_map = sorted(reading_map.items(), key=itemgetter(1), reverse=True)
                
    return templates.render('kanji', 
        kanji=kanji, 
        info=info, 
        reading_map = reading_map,
        reading_count = reading_count,
        kanji_count=data._all_kanji_count[kanji],
        kanji_total = data.get_kanji_total(),
        word_count = word_count,
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
        for article, sentences in reading_data['examples'].items():
            # add a tuple of sentenceNum and article
            for sentence_num in sentences:
                example_sentence_lookup[reading].add((sentence_num, article))
    
    #Go through all the example sentences
    all_sentences = {}
    for key in example_sentence_lookup:
        all_sentences[key] = data.populate_example_sentences(example_sentence_lookup[key], data.CONST_WORD_SENTENCE_LIMIT, word_info['readings'][key])                
    
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

@app.route('/word', methods=['GET'])
def show_all_words():
    page_num = 0
    search_content = ''
    if request.method == 'GET':
        if 'page' in request.args:
            page = request.args['page']
            if page.isdigit():
                page_num = int(page)-1
        if 'search' in request.args:
            search_content = request.args['search']
            if search_content: 
                word_list = data.search(search_content)
            else:
                word_list = data.get_valid_word_count()
        else:
            word_list = data.get_valid_word_count()
    
    start_slice = page_num*data.CONST_WORDS_PER_PAGE
    if start_slice >= len(word_list):
        start_slice = 0
        page_num = 0
        
    end_slice = (page_num+1)*data.CONST_WORDS_PER_PAGE
    if end_slice >= len(word_list):
        end_slice = len(word_list)
        
    return templates.render('allwords',
        search = search_content,
        num_pages = math.floor(len(word_list)/data.CONST_WORDS_PER_PAGE)+1,
        start_slice = start_slice,
        word_count=word_list[start_slice:end_slice],
        word_total = data.get_valid_word_total()
    )

@app.route('/search', methods=['GET']) 
def search():
    search_content = ''
    search_result = None
    if request.method == 'GET':
        if 'search' in request.args:
            search_content = request.args['search']
            if search_content: 
                if data.load_key(search_content):
                    search_result = data.tree.find(search_content)
    
    if search_result != None:
        sentences = data.populate_example_sentences(search_result, tree.CONST_SEARCH_SENTENCE_LIMIT)
        sentence_count = len(sentences)
    else:
        sentences = None
        sentence_count = 0
        
    return templates.render('search',
        result=sentences,
        search=search_content,
        sentence_count = sentence_count
    )
        
@app.route('/whyuse')
def why_use():
    return templates.render('whyuse')
    
@app.route('/confirmmail')
def confirm_email():
    return templates.render('confirmmail')
    
@app.route('/mailconfirmed')
def mail_confirmed():
    return templates.render('mailconfirmed')

class User():	
	def __init__(self, name, email, openid):
		self.name = name
		self.email = email
		self.openid = openid

@app.before_request
def before_request():
	g.user = None
	if 'openid' in session:
		# TODO: get user with openID same as session openID
		# g.user = User.query.filter_by(openid=session['openid']).first()
		i = 0 #random line to avoid error
	
@app.after_request
def after_request(response):
	#unconnect from DB
	return response

@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
	"""Does the login via OpenID. Has to call into `oid.try_login`
	to start the OpenID machinery.
	"""
	# if we are already logged in, go back to were we came from
	if g.user is not None:
		return redirect(oid.get_next_url())
	if request.method == 'POST':
		openid = request.form.get('openid')
		if openid:
			pape_req = pape.Request([])
			return oid.try_login(openid, ask_for=['email', 'nickname'],	extensions=[pape_req])
	
	return templates.render('login', next=oid.get_next_url(), error=oid.fetch_error())
	
@oid.after_login
def create_or_login(resp):
	"""This is called when login with OpenID succeeded and it's not
	necessary to figure out if this is the users's first login or not.
	This function has to redirect otherwise the user will be presented
	with a terrible URL which we certainly don't want.
	"""
	session['openid'] = resp.identity_url
	if 'pape' in resp.extensions:
		pape_resp = resp.extensions['pape']
		session['auth_time'] = pape_resp.auth_time
	
	#TODO: Get user with ID equal to "openid" variable
	#user = User.query.filter_by(openid=resp.identity_url).first()
	if user is not None:
		flash(u'Successfully signed in')
		g.user = user
		return redirect(oid.get_next_url())
	
	return redirect(url_for('create_profile', next=oid.get_next_url(), name=resp.fullname or resp.nickname, email=resp.email))
	
@app.route('/create-profile', methods=['GET', 'POST'])
def create_profile():
	"""If this is the user's first login, the create_or_login function
	will redirect here so that the user can set up his profile.
	"""
	if g.user is not None or 'openid' not in session:
		return redirect(url_for('index'))
	if request.method == 'POST':
		name = request.form['name']
		email = request.form['email']
		if not name:
			flash(u'Error: you have to provide a name')
		elif '@' not in email:
			flash(u'Error: you have to enter a valid email address')
		else:
			flash(u'Profile successfully created')
			# TODO: WE ADD TO DATABASE HERE
			return redirect(oid.get_next_url())
	return templates.render('create_profile', next_url=oid.get_next_url())

@app.route('/profile', methods=['GET', 'POST'])
def edit_profile():
	"""Updates a profile"""
	if g.user is None:
		abort(401)
	form = dict(name=g.user.name, email=g.user.email)
	if request.method == 'POST':
		if 'delete' in request.form:
			#Remove from DB here
			session['openid'] = None
			flash(u'Profile deleted')
			return redirect(url_for('index'))
		form['name'] = request.form['name']
		form['email'] = request.form['email']
		if not form['name']:
			flash(u'Error: you have to provide a name')
		elif '@' not in form['email']:
			flash(u'Error: you have to enter a valid email address')
		else:
			flash(u'Profile successfully created')
			g.user.name = form['name']
			g.user.email = form['email']
			# TODO: Update DB here
			return redirect(url_for('edit_profile'))
	return templates.render('edit_profile', form=form)
	
@app.route('/logout')
def logout():
	session.pop('openid', None)
	flash(u'You have been signed out')
	return redirect(oid.get_next_url())