"""Flask app for Upword"""

from flask import Flask, redirect, render_template, session, flash, request
from flask_debugtoolbar import DebugToolbarExtension
import requests, random
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file 
import os

from forms import AddUserForm, LoginForm, EditUserForm
from models import db, connect_db, User, Favorite 

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "a-secret"

# toolbar = DebugToolbarExtension(app)

connect_db(app)

# Get list of books and corresponding ids for random verse feature
response_books = requests.get('https://bolls.life/static/bolls/app/views/translations_books.json')
book_dict = {book['bookid']:book['name'] for book in response_books.json()['ESV']}
filtered_books = [19, 20, 43, 45, 46, 48, 49, 50, 51, 58, 59]

# set default translation 
translation = 'ESV'

# get list of translations in english
response_translations = requests.get('https://bolls.life/static/bolls/app/views/languages.json')
english = response_translations.json()[6] # this used to be index [4], but it looks like the API added more languages
translations = sorted([code['short_name'] for code in english['translations']])

@app.errorhandler(Exception)
def page_not_found(e):
    """ Show error page """
    return render_template('404.html', e=e)

@app.route("/")
def show_home():
    """ Show homepage """
    response_translation = requests.get(f'https://bolls.life/get-random-verse/{translation}/')
    response_translation.raise_for_status()
    
    bookid = random.choice(filtered_books) # picks random book
    chapters = response_books.json()['ESV'][bookid-1]['chapters'] # finds number of chapters in book
    chapterid = random.randint(1,chapters) # picks random chapter
    response_chapter = requests.get(f'https://bolls.life/get-chapter/{translation}/{bookid}/{chapterid}') 
    response_chapter.raise_for_status()
    verseid = random.randint(1,len(response_chapter.json())) # picks random verse
    response_verse = requests.get(f'https://bolls.life/get-verse/{translation}/{bookid}/{chapterid}/{verseid}')
    response_verse.raise_for_status()
    
    return render_template("home.html", random=response_translation.json(), chosen=response_verse.json(), book_dict=book_dict, 
                           translation=translation, book=bookid, chapter=chapterid, translations=translations)

################### User routes ###################

@app.route('/signup', methods=["GET", "POST"])
def signup():
    """ Create new user and add to db """
    form = AddUserForm()
    
    if form.validate_on_submit():
        try:
            user = User.signup(username=form.username.data,
                               password=form.password.data,
                               email=form.email.data)
            db.session.commit()
        
        except IntegrityError:
            flash('Username/email already taken', 'danger')
            return render_template('signup.html', form=form)

        session['username'] = user.username
        flash(f'Hello {user.username}!', 'success')
        return redirect('/')
        
    else: 
        return render_template('signup.html', form=form)

@app.route('/logout')
def logout():
    """ Log out user """
    
    if 'username' not in session:
        flash('Unauthorized request.', 'danger') 
        return redirect('/')
    
    session.pop('username')
    globals()['translation']='ESV'
    flash('You have been successfully logged out.', 'success')
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """ Display login user form """
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.login(username=form.username.data, password=form.password.data)
        
        if not user:
            flash('Incorrect login credentials.', 'danger')
            return render_template('login.html', form=form)

        session['username'] = user.username
        globals()['translation']=user.fav_translation
        flash(f'Hello, {user.username}!', 'success')
        return redirect('/favorites')
        
    else: 
        return render_template('login.html', form=form)
    
@app.route('/account', methods=['GET', 'POST'])
def edit_user():
    """ Display form to edit user details """
    
    if 'username' not in session:
        flash('Unauthorized request.', 'danger') 
        return redirect('/')
    
    user = User.query.filter_by(username=session['username']).first()
    form = EditUserForm(obj=user)
    
    form.fav_translation.choices = translations
    
    if form.validate_on_submit():
        try:
            user.username = form.username.data
            user.email = form.email.data
            user.first_name = form.first_name.data
            user.last_name = form.last_name.data
            user.fav_translation = form.fav_translation.data
            globals()['translation'] = form.fav_translation.data
            db.session.add(user)
            db.session.commit()
            session['username'] = user.username
            flash('Account updated successfully.', 'success')
            return redirect('/')
        
        except IntegrityError:
            flash('Username/email already taken', 'danger')
            return render_template('user_details.html', form=form)
    
    else:
        return render_template('user_details.html', form=form)
    
@app.route('/account/delete', methods=['POST'])
def delete_user():
    """Delete user from db"""
    
    if 'username' not in session:
        flash('Unauthorized request.', 'danger') 
        return redirect('/')
    
    user = User.query.filter_by(username=session['username']).first()
    db.session.delete(user)
    db.session.commit()
    
    session.pop('username')
    globals()['translation']='ESV'
    flash('You have successfully deleted your account.', 'success')
    return redirect('/signup')
    
    return redirect('/')    

################### Query routes ######################

@app.route('/search')
def search():
    """ Display keyword search results """
    result = request.args['search']
    user_search = requests.get(f'https://bolls.life/find/{translation}/?search={result}&match_case=false&match_whole=true')
    user_search.raise_for_status()
    
    return render_template('search.html', query=user_search.json(), search=result, book_dict=book_dict, num=len(user_search.json()))

@app.route('/verse')
def verse_lookup():
    """ Display search result of scripture input by user """
    result = request.args
    version = result['translation'] if result['translation'] else translation 
    bookid = int(result['book'])
    chapter = int(result['chapter'])
    data = dict() # dict of data for chapter, verses, translation, book
    
    if result['verse1']: # get verses
        
        verse1 = int(result['verse1'])
        verse2 = int(result['verse2']) if result['verse2'] else (verse1)
        verses = [*range(verse1, verse2 + 1)]   
        
        
        url = 'https://bolls.life/get-paralel-verses/'
        headers = {"Content-Type": "application/json"}
        body = {'translations': [version, version],
                        'verses': verses,
                        'book': bookid,
                        'chapter': chapter}
        response_verses = requests.post(url, headers=headers, json=body)
        response_verses.raise_for_status()

        if (response_verses.status_code == 400 or 'text' not in response_verses.json()[0][0]):
            flash('Scripture could not be found at this time, please try a different one.', 'warning')
            return redirect('/')
        
        return render_template('verse.html', text=response_verses.json()[0], book_dict=book_dict, data=data, verse2=verse2)

    else: # get chapter
        response_chapter = requests.get(f'https://bolls.life/get-chapter/{ version }/{ bookid }/{ chapter }/')
        response_chapter.raise_for_status()
        if (response_chapter.status_code == 404 or not response_chapter.json()):
            flash('Scripture could not be found at this time, please try a different one.', 'warning')
            return redirect('/')
    
        verses = response_chapter.json()
        data['verse'] = f'1-{len(verses)}'    
        data['book'] = book_dict[bookid]
        data['translation'] = version
        data['chapter'] = chapter
        return render_template('verse.html', verses=verses, data=data)

@app.route('/compare')
def compare_form():
    """ Show form to compare two translations"""
    return render_template('compare_form.html', book_dict=book_dict, translation=translation, translations=translations)

@app.route('/comparison')
def comparison():
    """ Display comparison of text """
    result = request.args
    bookid = int(result['book'])
    chapter = int(result['chapter'])
    version1 = result['translation1'] if result['translation1'] else translation
    version2 = result['translation2'] if result['translation2'] else translation 

    response_chapter = requests.get(f'https://bolls.life/get-chapter/{translation}/{bookid}/{chapter}') 
    response_chapter.raise_for_status()
    if response_chapter.status_code == 404:
        flash('Scripture could not be found at this time, please try a different one.', 'warning')
        return render_template('compare_form.html', book_dict=book_dict, translation=translation, translations=translations)
    
    verses = [*range(1, len(response_chapter.json()))]
    
    url = 'https://bolls.life/get-paralel-verses/'
    headers = {"Content-Type": "application/json"}
    body = {'translations': [version1, version2],
                    'verses': verses,
                    'book': bookid,
                    'chapter': chapter}
    response_comparison = requests.post(url, headers=headers, json=body)
    response_comparison.raise_for_status()
    
    if response_comparison.status_code == 400:
        flash('Scripture could not be found at this time, please try a different one.', 'warning')
        return render_template('compare_form.html', book_dict=book_dict, translation=translation, translations=translations)
     
    return render_template('comparison.html', result=response_comparison.json(), book_dict=book_dict, translation=translation, translations=translations)

################### Favorites ###################

@app.route('/favorites')
def show_favs():
    """ Show list of users favorite verses """
    if 'username' not in session:
        flash('Unauthorized request.', 'danger') 
        return redirect('/login')
    
    user = User.query.filter_by(username=session['username']).first()
    faves = Favorite.query.filter_by(user_id = user.id).order_by(Favorite.id.desc()).all()
    
    return render_template('favorites.html', faves=faves, book_dict=book_dict, translation=translation, translations=translations)

@app.route('/add-favorite/<int:book>/<int:chapter>/<int:verseID>')
def add_fave(book, chapter, verseID):
    """ Adds verse to favorite """
    response_verse = requests.get(f'https://bolls.life/get-verse/{ translation }/{ book }/{ chapter }/{ verseID }/')        
    response_verse.raise_for_status()
    verse = response_verse.json()
    verse['bookid'] = book
    verse['book'] = book_dict[book]
    verse['chapter'] = chapter
    verse['translation'] = translation
    user = User.query.filter_by(username=session['username']).first()
    fave = Favorite(user_id=user.id, book_code=book, book=verse['book'], chapter=chapter,
                    verse=verseID, num_of_verses=1, text=verse['text'], translation=translation)
    db.session.add(fave)
    db.session.commit()
    return redirect('/favorites')

@app.route('/add-section', methods=['POST'])
def add_section():
    """ Adds a section of verses to favorites from within favorties route """
    result = request.form
    if result:
        bookid = int(result['book'])
        chapter = int(result['chapter'])
        version = result['translation'] if result['translation'] else translation
        verse1 = int(result['verse1'])
        verse2 = int(result['verse2']) if result['verse2'] else (verse1)
        verses = [*range(verse1, verse2 + 1)]
        
        url = 'https://bolls.life/get-paralel-verses/'
        headers = {"Content-Type": "application/json"}
        body = {'translations': [version, version],
                        'verses': verses,
                        'book': bookid,
                        'chapter': chapter}
        response_verses = requests.post(url, headers=headers, json=body)
        response_verses.raise_for_status()
        if (response_verses.status_code == 400 or 'text' not in response_verses.json()[0][0]):
            flash('Scripture could not be found at this time, please try a different one.', 'warning')
            return redirect('/favorites')
        
        temp = response_verses.json()[0]
        text = ' '.join([text['text'] for text in temp]) # joins list of verses together to be stored in DB
        user = User.query.filter_by(username=session['username']).first()
    
        fave = Favorite(user_id=user.id, book_code=bookid, book=book_dict[bookid], chapter=chapter,
                        verse=verse1, num_of_verses=len(verses), text=text, translation=version)
        db.session.add(fave)
        db.session.commit() 
        
    return redirect('/favorites')
    
@app.route('/favorites/<int:fave_id>/delete')
def delete_fave(fave_id):
    """ Removes favorite verse from DB """
    fave = Favorite.query.filter_by(id=fave_id).first()
    db.session.delete(fave)
    db.session.commit()
    
    flash(f'Verse(s) from {fave.book} has been removed from your favorites.', 'warning')
    return redirect('/favorites')


################### Memory Game ###################

@app.route('/game')
def show_game():
    """ Render memory game """
    result = request.args
    if result:
        bookid = int(result['book'])
        chapter = int(result['chapter'])
        version = result['translation'] if result['translation'] else translation
        verse1 = int(result['verse1'])
        verse2 = int(result['verse2']) if result['verse2'] else (verse1)
        verses = [*range(verse1, verse2 + 1)]
        
        url = 'https://bolls.life/get-paralel-verses/'
        headers = {"Content-Type": "application/json"}
        body = {'translations': [version, version],
                        'verses': verses,
                        'book': bookid,
                        'chapter': chapter}
        response_verses = requests.post(url, headers=headers, json=body)
        response_verses.raise_for_status()
        if (response_verses.status_code == 400 or 'text' not in response_verses.json()[0][0]):
            flash('Scripture could not be found at this time, please try a different one.', 'warning')
            return redirect('/game')
        
        temp = response_verses.json()[0] 
        for text in temp: # splits up text to allow for styling of individual words
            if 'text' in text:
                text['text'] = text['text'].split()
        
        return render_template('game.html', result=temp, book_dict=book_dict, translation=translation, translations=translations)

        
    return render_template('game.html', result=None, book_dict=book_dict, translation=translation, translations=translations)