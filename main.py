# Iurii Dziuban -- https://iuriid.github.io/ -- iurii.dziuban@gmail.com -- Nov-Dec 2017

# My 1st real miniproject. Started on ~01.11.2017 after learning Python/coding for ~175 hours (3-3.5months) in total.
# Major version 1.0 (with user management, preferences and charting with both pygal and plot.ly finished on 02.01.2018, ~248h, delta=73h)
# This service which during development was called 'Car-price-age-mileage' or CPAM requests data for a given car model
# from auto.ria.ua using their API (https://github.com/ria-com/auto-ria-rest-api) and draws scatter charts (using 2 charting
# engines/libraries - pygal and plot.ly) for age & price, price & mileage and age & mileage.
# Has user management system (register, login, profile update, password update, password reset, avatar) and a preferences
# page where user can change 2 parameters: adverticements quantity for the model being analyzed (5-50; auto.ria.ua API's)
# restriction is 500 requests/hour) and charting engine. Uses MongoDB, Flask, pygal, plot.ly

# At deployment makemodels2DB.py script should be run manually which creates a MongoDB 'makemodels' with 2 collections:
# 1) 'makes" ('make name/make ID') and
# 2) 'makesmodelscll' ('make name/make ID/model name/model ID').
# All data used for charting (price/age/mileage and ads IDs) are stored in MongoDB 'makemodels', in collections 'X-Y',
# where 'X' - make ID, 'Y' - model ID. Collections for each model are updated at every request if needed.

import os
import imghdr
import requests, json, plotly, pygal
from flask import Flask, render_template, url_for, session, request, redirect, flash
from wtforms import Form, StringField, PasswordField, SelectField, TextAreaField, FileField, RadioField, IntegerField
from wtforms.validators import Length, DataRequired, Email, EqualTo, NumberRange
from flask_bootstrap import Bootstrap
from pymongo import MongoClient
from cpam_functions import simplifydic, get_price_age_mileage
from keys import api_key, app_secret_key, mail_pwd
from passlib.hash import sha256_crypt
from functools import wraps
from flask_mail import Mail, Message
import string, random

app = Flask(__name__)
bootstrap = Bootstrap(app)
app.secret_key = app_secret_key

mail = Mail(app)
app.config.update(
    DEBUG=True,
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_SSL=False,
    MAIL_USE_TLS=True,
    MAIL_USERNAME = 'mailvulgaris@gmail.com',
    MAIL_PASSWORD = mail_pwd
)
# ! need to reinitialize!
mail = Mail(app)

# Prepare a list of makes/models for index page
client = MongoClient()
db = client.makemodels
makesmodelscll = db.makesmodelscll  # collection for 'make name/make ID/model name/model ID's (~3.7k docs)
mks = db.makes  # collection for 'make name/make ID's (~265 docs)

# Prepare a list of makes
makes = []
for doc in mks.find():
    makes.append(doc['make'])
makes = sorted(makes)

# Prepare a list of urls ('/make_name/model_name')
makemodellist = []
for make in makes:
    models4make = []
    for doc in makesmodelscll.find({'make': make}):
        models4make.append('/' + doc['make'] + '/' + doc['model'])
    # Make a list in format [[make_name1, [model_name1, model_name2, model_name3, ...]], [make_name2, [model_name1, model_name2, model_name3, ...]], ...]
    makemodellist.append([make, sorted(models4make)])
    makemodellist = sorted(makemodellist)
    makemodeloutput = []
    for make in makemodellist:
        for model in make[1]:
            modelname = model.split('/')[1]+' '+model.split('/')[2]
            makemodeloutput.append((model, modelname))

class IndexForm(Form):
    makemodels = SelectField('', choices=makemodeloutput)

class RegistrationForm(Form):
    username = StringField('Username', validators=[Length(4, 20)])
    email = StringField('Email Address', validators=[Length(6, 50), DataRequired(), Email()])
    password = PasswordField('New Password', validators=[DataRequired(), EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Repeat Password')

class LoginForm(Form):
    usernameoremail = StringField('Username or Email Address', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class ProfileForm(Form):
    username = StringField('Username', validators=[Length(4, 20)])
    email = StringField('Email Address', validators=[Length(6, 50), DataRequired(), Email()])
    language = SelectField('Language', choices=[('en', 'en'), ('ua', 'ua'), ('ru', 'ru')])
    description = TextAreaField('Description', validators=[Length(max=256)])

class UploadForm(Form):
    image_file = FileField('')

class PasswordReset(Form):
    email = StringField('Email Address', validators=[Length(6, 50), DataRequired(), Email()])

class PasswordUpdate(Form):
    oldpassword = PasswordField('Old password', validators=[DataRequired()])
    newpassword = PasswordField('New password', validators=[DataRequired(), EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Repeat new password')

class Unregister(Form):
    password = PasswordField('Password', validators=[DataRequired()])

class Preferences(Form):
    # /preferences - allows user to customise some service features. So far:
    # 1) change 'ads_analysed' parameter (from 5 to 50)
    # 2) select charting engine, plot.ly or pygal
    ads_qty = IntegerField('Quantity of adverticements analysed for each model (5-50)', validators=[DataRequired(), NumberRange(5, 50, 'Adverticements quantity should be between %(min)s and %(max)s')])
    charting_tool = RadioField('Charting engine', choices=[('pltly', 'Plot.ly'), ('pgl', 'Pygal')])

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('You need to login first', 'alert alert-warning')
            return redirect(url_for('login'))
    return wrap

def notloggedin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            flash('You need to <a href="/logout">log out</a> first.', 'alert alert-warning')
            return redirect(url_for('index'))
        else:
            return f(*args, **kwargs)
    return wrap
#
# Let's make an index page with a list of models for user to choose from
# Flask decorator, index page
@app.route('/index/', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        indexform = IndexForm(request.form)
        #flash(makemodeloutput)

        # POST-request
        if request.method == 'POST' and indexform.validate():
            makemodelurl = indexform.makemodels.data
            return redirect(makemodelurl)

        # the first (GET) request for a index page
        return render_template('index.html', makemodellist=makemodellist, indexform=indexform)

    except Exception as e:
        # 2be removed in final version
        #flash(e, 'alert alert-danger')
        return redirect(url_for('index'))


# A page with charts for a model chosen by user
@app.route('/<make>/<model>')
def getcharts(make, model):
    client = MongoClient()
    db = client.makemodels
    makesmodelscll = db.makesmodelscll # collection for 'make name/make ID/model name/model ID's (~3.7k docs)

    # If user is logged in - check DB to determine his preferences (ads quantity to be analysed [default = 20] and charting engine [default = plot.ly ('pltly')]
    # Retrieve from user's data in DB the ads number to be requested (if user logged in)
    if 'logged_in' in session:
        users = client.db.users  # collection 'users' in 'db' database
        docID = None
        username = session['username']  # getting username from session variable (to determine document's ID)
        docID = users.find_one({'username': username}).get('_id')
        ads_analysed = users.find_one({'_id': docID})['ads_qty']
        charting_tool = users.find_one({'_id': docID})['charting_tool']
    else:
        ads_analysed = 20 # quantity of adverticements requested for analysis
        charting_tool = 'pltly'

    # For a given make and model get make_ID and model_ID from DB
    makeID = makesmodelscll.find_one({'make': make})['make_id']
    modelID = makesmodelscll.find_one({'make': make, 'model': model})['model_id']

    # Make requests to auto.ria.ua API and get IDs of adverticements for given model
    r3 = requests.get('https://developers.ria.com/auto/search?api_key=' + api_key + '&category_id=1&marka_id=' + str(
        makeID) + '&model_id=' + str(modelID) + '&countpage=' + str(ads_analysed))
    parsed_IDs = json.loads(r3.text)
    adsIDlist = []
    adsIDstr = parsed_IDs['result']['search_result']['ids']
    for id in adsIDstr:
        adsIDlist.append(int(id))
    # We'll display an alert before charts if there are less than 5 ads on auto.ria.ua for a given model
    toofewads = False
    if len(adsIDlist)<5:
        toofewads = True

    # Check if any ads for given model exist. If no - abort further steps and render charts.html with
    # notice "Sorry, but no adverticements were found for this model, can't build charts. Please choose another model"
    if not adsIDlist:
        return render_template('charts.html', nodata=True, make=make, model=model)

    # If we have at least 1 ads for a given model, proceed:
    else:
        # Get price/age/mileage data for each ads
        finaldatajson = []  # list of dictionaries in format [{'ads_id': ads1id, 'price': price1, 'age': age1, 'mileage': mileage1}, {'ads_id': ads2id, 'price': price2, 'age': age2, 'mileage': mileage2}, ...]
        for adsid in adsIDlist:
            r4 = requests.get('https://developers.ria.com/auto/info?api_key=' + api_key + '&auto_id=' + str(adsid))
            parsed_ads = json.loads(r4.text)
            finaldatajson.append(get_price_age_mileage(parsed_ads))

        # So now we have a list of ads requested from auto.ria.ua
        # Let's check if we already have a collection of ads for this model (named 'makeID-modelID')
        collectionname = str(makeID)+'-'+str(modelID)
        if collectionname in db.collection_names():
            # If 'yes', let's retrieve these data from db,
            alreadyindb = [] # list of dictionaries in format [{'ads_id': ads1id, 'price': price1, 'age': age1, 'mileage': mileage1}, {'ads_id': ads2id, 'price': price2, 'age': age2, 'mileage': mileage2}, ...]
            for post in db[collectionname].find():
                alreadyindb.append({'ads_id': post['ads_id'], 'price': post['price'], 'age': post['age'], 'mileage': post['mileage']})
            # we may have 1) new ads that are absent in db, 2) ads that's already in db and 3) ads in db that were absent in our request
            # we shall add to db ads belonging to cat. #1, update if needed, ads cat. #2 and delete ads cat. #3
            # Iterate through our existing data
            for dic in alreadyindb:
                oldadsID = dic['ads_id']

                # Retrieve our new ads with the same ID
                newads = next((item for item in finaldatajson if item["ads_id"] == oldadsID), False)
                # If a document for ads that's already in our db coinsides with a requested ads - update it if needed (price, age, mileage)
                if newads:
                    # Our old ads = 'dic'
                    # Get old price, age, mileage
                    pricewas = dic['price']
                    agewas = dic['age']
                    mileagewas = dic['mileage']
                    # Get new price, age, mileage
                    newprice = newads['price']
                    newage = newads['age']
                    newmileage = newads['mileage']
                    priceflag, ageflag, mileageflag = False, False, False
                    datatoupdate = {}
                    if pricewas!=newprice:
                        datatoupdate['price']=newprice
                        priceflag = True
                    if agewas!=newage:
                        datatoupdate['age']=newage
                        ageflag = True
                    if mileagewas!=newmileage:
                        datatoupdate['mileage']=newmileage
                        mileageflag = True
                    if priceflag or ageflag or mileageflag:
                        db[collectionname].update_one({'ads_id': oldadsID}, {'$set': datatoupdate}) # Go update the document in db with new values
                # If we have a document in our collection which is absent in our new request - delete it from collection
                else:
                    db[collectionname].delete_one({'ads_id': oldadsID})
            # Also we have to iterate through our new ads to find such ones that were'nt added to our collection yet and add them
            for dic in finaldatajson:
                newadsID = dic['ads_id']
                if not next((item for item in alreadyindb if item["ads_id"] == newadsID), False):
                    db[collectionname].insert_one(dic)

        # If we don't have a collection of ads for this model, create it and populate with ads
        else:
            result = db[collectionname].insert_many(finaldatajson)


        # Let's draw charts. Retrieve price-age-mileage data from DB
        datafromdb = []
        for post in db[collectionname].find():
            datafromdb.append([post['ads_id'], post['price'], post['age'], post['mileage']])

        price_age_chart_name = 'Price($) vs. Age (years): ' + make + '-' + model
        price_mileage_chart_name = 'Price($) vs. Mileage (x1000km): ' + make + '-' + model
        mileage_age_chart_name = 'Age (years) vs. Mileage (x1000km): ' + make + '-' + model



        ages, prices, mileages, adsids = [], [], [], []

        if charting_tool == 'pgl':
            # Draw charts using pygal lib
            price_age_XY = pygal.XY(stroke=False, show_legend=False, human_readable=True, fill=False,
                                    title=u'Price($) vs. Age (years): ' + make + '-' + model,
                                    x_title='Age (years)', y_title='Price ($)', tooltip_border_radius=10, dots_size=5, width=600, height=600)
            price_mileage_XY = pygal.XY(stroke=False, show_legend=False, human_readable=True, fill=False,
                                        title=u'Price($) vs. Mileage (x1000km): ' + make + '-' + model,
                                        x_title='Mileage (x1000km)', y_title='Price ($)', tooltip_border_radius=10, dots_size=5, width=600, height=600)
            mileage_age_XY = pygal.XY(stroke=False, show_legend=False, human_readable=True, fill=False,
                                      title=u'Age (years) vs. Mileage (x1000km): ' + make + '-' + model,
                                      x_title='Mileage (x1000km)', y_title='Age (years)', tooltip_border_radius=10, dots_size=5, width=600, height=600)

            for every_ads in datafromdb:
                price_age_XY.add(str(every_ads[0]), [[every_ads[2], every_ads[1]]])
                price_mileage_XY.add(str(every_ads[0]), [[every_ads[3], every_ads[1]]])
                mileage_age_XY.add(str(every_ads[0]), [[every_ads[3], every_ads[2]]])

            ch_pa = 'static/' + make + '-' + model + '-' + 'price_age.svg' # name of chart price-age
            ch_pm = 'static/' + make + '-' + model + '-' + 'price_mileage.svg' # name of chart price-mileage
            ch_ma = 'static/' + make + '-' + model + '-' + 'age_mileage.svg'# name of chart mileage-age

            price_age_XY.render_to_file(ch_pa)
            price_mileage_XY.render_to_file(ch_pm)
            mileage_age_XY.render_to_file(ch_ma)

            ch_pa = '/' + ch_pa + '?' + str(random.randint(1,10000))
            ch_pm = '/' + ch_pm + '?' + str(random.randint(1,10000))
            ch_ma = '/' + ch_ma + '?' + str(random.randint(1,10000))

            if toofewads==True:
                return render_template('charts.html', nodata=False, toofewads=True, make=make, model=model, charting_tool=charting_tool, ch_pa=ch_pa, ch_pm=ch_pm,
                                       ch_ma=ch_ma)
            else:
                return render_template('charts.html', nodata=False, toofewads=False, make=make, model=model, charting_tool=charting_tool, ch_pa=ch_pa,
                                       ch_pm=ch_pm, ch_ma=ch_ma)

        else:
            # Draw charts using plot.ly
            for every_ads in datafromdb:
                # Plot.ly
                ages.append(every_ads[2])
                prices.append(every_ads[1])
                mileages.append(every_ads[3])
                adsids.append(every_ads[0])

            graphs = [
                dict(
                    data=[
                        dict(
                            x=ages,
                            y=prices,
                            text=adsids,
                            type='scatter',
                            mode='markers',
                            marker={'color': 'red', 'size': '15', 'opacity': 0.5, 'line': {'width': 0.75, 'color': 'white'}}
                        ),
                    ],
                    layout=dict(
                        title=price_age_chart_name,
                        xaxis={'title': 'Age (years)'}, yaxis={'title': 'Price ($)'},
                        width=700, height=600
                    )
                ),
                dict(
                    data=[
                        dict(
                            x=mileages,
                            y=prices,
                            text=adsids,
                            type='scatter',
                            mode='markers',
                            marker={'color': 'blue', 'size': '15', 'opacity': 0.5, 'line': {'width': 0.75, 'color': 'white'}}
                        ),
                    ],
                    layout=dict(
                        title=price_mileage_chart_name,
                        xaxis={'title': 'Mileage (x1000km)'}, yaxis={'title': 'Price ($)'},
                        width=700, height=600
                    )
                ),
                dict(
                    data=[
                        dict(
                            x=ages,
                            y=mileages,
                            text=adsids,
                            type='scatter',
                            mode='markers',
                            marker={'color': 'green', 'size': '15', 'opacity': 0.5, 'line': {'width': 0.75, 'color': 'white'}}
                        ),
                    ],
                    layout=dict(
                        title=mileage_age_chart_name,
                        xaxis={'title': 'Age (years)'}, yaxis={'title': 'Mileage (x1000km)'},
                        width=700, height=600
                    )
                )
            ]

            ids = ['graph-{}'.format(i) for i, _ in enumerate(graphs)]
            graphJSON = json.dumps(graphs, cls=plotly.utils.PlotlyJSONEncoder)

            if toofewads==True:
                return render_template('charts.html', nodata=False, toofewads=True, make=make, model=model, charting_tool=charting_tool, ids=ids, graphJSON=graphJSON)
            else:
                return render_template('charts.html', nodata=False, toofewads=False, make=make, model=model, charting_tool=charting_tool, ids=ids, graphJSON=graphJSON)

@app.route('/register/', methods=['GET', 'POST'])
@notloggedin_required
def register():
    try:
        form = RegistrationForm(request.form)

        # registration data have been submitted (POST)
        if request.method == 'POST' and form.validate():
            username = form.username.data
            email = form.email.data
            password = sha256_crypt.encrypt(str(form.password.data))

            client = MongoClient()
            db = client.db
            users = db.users  # collection 'users' in 'db' database

            # Let's check if username isn't already in our collection
            # He/she may be there already but 'soft-deleted' (already registered but then unregistered ['status': 'active' >> 'status': 'inactive'])
            docID = None
            status = None
            if users.find_one({'username': username}):
                docID = users.find_one({'username': username}).get('_id')
                status = users.find_one({'_id': docID}).get('status')
            if users.find_one({'email': email}):
                docID = users.find_one({'email': email}).get('_id')
                status = users.find_one({'_id': docID}).get('status')

            if (users.find_one({'username': username}) or users.find_one({'email': email})) and status == 'active':
                flash('Sorry, but this username or email are already taken. Please choose different credentials or <a href="/login">login</a>', 'alert alert-warning')
                return render_template('register.html', form=form)
            else:
                if status == 'inactive':
                    users.remove({'_id': docID})
                users.insert_one({'username': username, 'email': email, 'password': password, 'status': 'active', 'language': 'en', 'description': '', 'avatar': 'default.jpg', 'ads_qty': 20, 'charting_tool': 'pltly'})
                session['logged_in'] = True
                session['username'] = username
                flash('Registration successfull! <a href="/logout/">Logout</a> or go to your <a href="/profile">profile</a>', 'alert alert-success')
                return redirect(url_for('index'))

        # the first (GET) request for a registration form
        return render_template('register.html', form=form)

    except Exception as e:
        # 2be removed in final version
        #flash(e, 'alert alert-danger')
        return redirect(url_for('index'))

@app.route('/login/', methods=['GET', 'POST'])
@notloggedin_required
def login():
    try:
        loginform = LoginForm(request.form)

        # login data have been submitted (POST)
        if request.method == 'POST' and loginform.validate():
            usernameoremail = loginform.usernameoremail.data
            password = loginform.password.data

            client = MongoClient()
            db = client.db
            users = db.users  # collection 'users' in 'db' database

            # let's check for this login in usernames or emails and if such user exists - let's check if it is not 'inactive' (unregistered)
            docID = None
            username = ''
            if users.find_one({'username': usernameoremail}):
                docID = users.find_one({'username': usernameoremail}).get('_id')
                status = users.find_one({'_id': docID}).get('status')
                if status == 'active':
                    username = usernameoremail
                else:
                    flash(
                        'Sorry, we do not recognize this username or email address. Please choose different credentials or <a href="/register/">register</a>',
                        'alert alert-warning')
                    return render_template('login.html', loginform=loginform)
            elif users.find_one({'email': usernameoremail}):
                docID = users.find_one({'email': usernameoremail}).get('_id')
                status = users.find_one({'_id': docID}).get('status')
                if status == 'active':
                    username = users.find_one({'_id': docID})['username']
                else:
                    flash(
                        'Sorry, we do not recognize this username or email address. Please choose different credentials or <a href="/register/">register</a>',
                        'alert alert-warning')
                    return render_template('login.html', loginform=loginform)
            else:
                flash(
                    'Sorry, we do not recognize this username or email address. Please choose different credentials or <a href="/register/">register</a>',
                    'alert alert-warning')
                return render_template('login.html', loginform=loginform)

            # and then let's check for a password
            pwd_should_be = users.find_one({'_id': docID})['password']
            if sha256_crypt.verify(password, pwd_should_be):
                session['logged_in'] = True
                session['username'] = username
                flash('Login successfull!',
                      'alert alert-success')
                return redirect(url_for('index'))
            # invalid password
            else:
                flash('Wrong password', 'alert alert-danger')
                return render_template('login.html', loginform=loginform)

        # the first (GET) request for a login form
        return render_template('login.html', loginform=loginform)

    except Exception as e:
        # 2be removed in final version
        #flash(e, 'alert alert-danger')
        return redirect(url_for('index'))

@app.route('/logout/')
@login_required
def logout():
    session.clear()
    flash(
        'You have been logged out', 'alert alert-success')
    return redirect(url_for('index'))

@app.route('/profile/', methods=['GET', 'POST'])
@login_required
def profile():
    try:
        # let's retrieve from db data to prepopulate profile form (username, email, language selected, description)
        client = MongoClient()
        db = client.db
        users = db.users  # collection 'users' in 'db' database
        docID = None

        username = session['username']  # getting username from session variable (to determine document's ID)
        docID = users.find_one({'username': username}).get('_id')
        email = users.find_one({'_id': docID})['email']
        lang = users.find_one({'_id': docID})['language']
        description = users.find_one({'_id': docID})['description']
        # flash(str(docID)) # temp
        person = {'username': username, 'email': email, 'language': lang, 'description': description}
        # flash(str(person))  # temp

        if request.method == 'POST':
            profileform = ProfileForm(request.form)
            if profileform.validate():
                # save updated data to db
                # check for data to be updated
                # flash('POST request ok')  # temp
                datatoupdate = {}
                '''flash(profileform.username.data)
                flash(profileform.email.data)
                flash(profileform.language.data)
                flash(profileform.description.data)'''
                userflag, emailflag, langflag, descrflag = False, False, False, False

                if username != profileform.username.data:
                    # need to check if new username doesn't already exist in our DB
                    if users.find_one({'username': profileform.username.data}):
                        flash(
                            'Sorry, but this username is already taken by another user. Please choose a different one',
                            'alert alert-warning')
                        return render_template('profile.html', profileform=profileform)
                    else:
                        userflag = True
                        datatoupdate['username'] = profileform.username.data
                        session['username'] = profileform.username.data
                if email != profileform.email.data:
                    # need to check if new email doesn't already exist in our DB
                    if users.find_one({'email': profileform.email.data}):
                        flash(
                            'Sorry, but this email is already taken by another user. Please choose a different one',
                            'alert alert-warning')
                        return render_template('profile.html', profileform=profileform)
                    else:
                        emailflag = True
                        datatoupdate['email'] = profileform.email.data
                if lang != profileform.language.data:
                    langflag = True
                    datatoupdate['language'] = profileform.language.data
                if description != profileform.description.data:
                    descrflag = True
                    datatoupdate['description'] = profileform.description.data
                # flash(str(datatoupdate))  # temp
                if userflag or emailflag or langflag or descrflag:
                    # flash('Updating DB') # temp
                    users.update_one({'_id': docID},
                                     {'$set': datatoupdate})
                    flash(
                        'Profile successfully updated. Now you can go to the <a href="/">main page</a>, <a href="/preferences">preferences</a> or <a href="/logout">logout</a>.',
                        'alert alert-success')
            return render_template('profile.html', profileform=profileform)

        # GET request
        profileform = ProfileForm(data=person)
        return render_template('profile.html', profileform=profileform)

    except Exception as e:
        # 2be removed in final version
        #flash(e, 'alert alert-danger')
        return redirect(url_for('index'))

@app.route('/avatar/', methods=['GET', 'POST'])
@login_required
def avatar():
    try:
        # get the name for the avatar image from DB (by default = default.jpg, else - str(_id).jpg)
        client = MongoClient()
        db = client.db
        users = db.users  # collection 'users' in 'db' database
        docID = None
        username = session['username']  # getting username from session variable (to determine document's ID)
        docID = users.find_one({'username': username}).get('_id')
        image = '../static/uploads/' + users.find_one({'_id': docID})['avatar'] + '?' + str(
            random.randint(1, 10000))
        # flash(image) # temp
        # flash(str(docID)) # temp

        avatarform = UploadForm()

        if request.method == 'POST':
            if request.files['image_file'].filename == '':
                flash('Looks like you didn\'t select any file to upload. Please choose one',
                      'alert alert-warning')
                return render_template('avatar.html', avatarform=avatarform, image=image)
            if request.files['image_file'].filename[-4:].lower() != '.jpg':
                flash('Invalid file extension. Only .jpg/.jpeg images allowed',
                      'alert alert-warning')
                return render_template('avatar.html', avatarform=avatarform, image=image)
            if imghdr.what(request.files['image_file']) != 'jpeg':
                flash(
                    'Invalid image format. Are you sure that\'s really a .jpeg image? Please choose a different one',
                    'alert alert-warning')
                return render_template('avatar.html', avatarform=avatarform, image=image)

            path = 'uploads/' + str(docID) + '.jpg'
            request.files['image_file'].save(os.path.join(app.static_folder, path))
            users.update_one({'_id': docID}, {'$set': {'avatar': str(docID) + '.jpg'}})
            # avoid image caching
            image = '../static/uploads/' + str(docID) + '.jpg' + '?' + str(random.randint(1, 10000))
            # flash(image) # temp
            flash(
                'Avatar successfully updated!', 'alert alert-success')
        return render_template('avatar.html', avatarform=avatarform, image=image)

        # GET request
        return render_template('avatar.html', avatarform=avatarform, image=image)

    except Exception as e:
        # 2be removed in final version
        #flash(e, 'alert alert-danger')
        return redirect(url_for('index'))

@app.route('/password_reset/', methods=['GET', 'POST'])
def password_reset():
    try:
        # password is reset in case user forgot it and can't log in
        # any valid email can be entered, which will be checked against our DB if such user exists
        pwdresetform = PasswordReset(request.form)

        if request.method == 'POST' and pwdresetform.validate():
            newemail = pwdresetform.email.data

            client = MongoClient()
            db = client.db
            users = db.users  # collection 'users' in 'db' database

            # if entered email is absent in our DB
            if not users.find_one({'email': newemail}):
                flash('No users found with such email. Please provide a correct email address',
                      'alert alert-warning')
                return render_template('password_reset.html', pwdresetform=pwdresetform)
            else:
                # generate new password
                alphabet = string.ascii_letters + string.digits
                newpassword = ''.join(random.choice(alphabet) for i in range(12))
                # flash(newpassword) # temp

                # and send it to user
                msg = Message('You new password', sender="from@example.com", recipients=[newemail])
                msg.html = 'Here\'s your new password: ' + newpassword + '<br> You can change it using <a href="#">password update</a> form'
                mail.send(msg)
                # and also update it in our DB
                users.update_one({'email': newemail}, {'$set': {'password': sha256_crypt.encrypt(newpassword)}})
                flash(
                    'Password successfully updated! Please check your inbox. You can change this password using the <a href="/password_update">password update</a> form',
                    'alert alert-success')
            return redirect(url_for('index'))

        # GET request
        return render_template('password_reset.html', pwdresetform=pwdresetform)

    except Exception as e:
        # 2be removed in final version
        #flash(e, 'alert alert-danger')
        return redirect(url_for('index'))

@app.route('/password_update/', methods=['GET', 'POST'])
@login_required
def password_update():
    try:
        pwdupdateform = PasswordUpdate(request.form)

        if request.method == 'POST' and pwdupdateform.validate():
            # so now we have new password entered twice and some 'old' password
            # need to check the old one against our DB
            oldpwd = pwdupdateform.oldpassword.data

            client = MongoClient()
            db = client.db
            users = db.users  # collection 'users' in 'db' database

            # to update password user mush log in so we know username
            docID = None
            username = session['username']
            docID = users.find_one({'username': username}).get('_id')
            oldpwd_in_db = users.find_one({'_id': docID})['password']

            if not sha256_crypt.verify(oldpwd, oldpwd_in_db):
                flash('Old password not found. Please enter a valid old password',
                      'alert alert-warning')
                return render_template('password_update.html', pwdupdateform=pwdupdateform)
            else:
                # old password correct. New password can't be equal to the old one
                if pwdupdateform.oldpassword.data == pwdupdateform.newpassword.data:
                    flash(
                        'Sorry, but the new password can\'t be the same as the old one. Please choose a different new password',
                        'alert alert-warning')
                    return render_template('password_update.html', pwdupdateform=pwdupdateform)
                else:
                    # store new password to DB. Redirect to profile and inform user
                    users.update_one({'_id': docID}, {
                        '$set': {'password': sha256_crypt.encrypt(str(pwdupdateform.newpassword.data))}})
                    flash('Password successfully updated!', 'alert alert-success')
                    return redirect(url_for('profile'))
        return render_template('password_update.html', pwdupdateform=pwdupdateform)

        # GET request
        return render_template('password_update.html', pwdupdateform=pwdupdateform)

    except Exception as e:
        # 2be removed in final version
        #flash(e, 'alert alert-danger')
        return redirect(url_for('index'))

@app.route('/unregister/', methods=['GET', 'POST'])
@login_required
def unregister():
    try:
        unregform = Unregister(request.form)

        if request.method == 'POST' and unregform.validate():
            # input has been formally validated but need to check password agains our DB
            pwd = unregform.password.data

            client = MongoClient()
            db = client.db
            users = db.users  # collection 'users' in 'db' database
            docID = None

            username = session['username']
            docID = users.find_one({'username': username}).get('_id')
            pwd_in_db = users.find_one({'_id': docID})['password']

            if not sha256_crypt.verify(pwd, pwd_in_db):
                flash('Incorrect password. Try again', 'alert alert-warning')
                return render_template('unregister.html', unregform=unregform)
            else:
                # soft-delete account - change 'status' field in DB from 'active' to 'inactive'
                users.update_one({'_id': docID}, {'$set': {'status': 'inactive'}})
                session.clear()
                flash(
                    'Account successfully deleted. We will be missing you ;) <a href="/login">Login</a> or <a href="/register">register</a>',
                    'alert alert-success')
                return redirect(url_for('index'))
        return render_template('unregister.html', unregform=unregform)

        # GET request
        return render_template('unregister.html', unregform=unregform)

    except Exception as e:
        # 2be removed in final version
        #flash(e, 'alert alert-danger')
        return redirect(url_for('index'))

@app.route('/preferences/', methods=['GET', 'POST'])
@login_required
def preferences():
    try:
        # let's retrieve from db data to prepopulate profile form (username, email, language selected, description)
        client = MongoClient()
        db = client.db
        users = db.users  # collection 'users' in 'db' database
        docID = None

        username = session['username']  # getting username from session variable (to determine document's ID)
        docID = users.find_one({'username': username}).get('_id')
        charting_tool = users.find_one({'_id': docID})['charting_tool']
        ads_qty = users.find_one({'_id': docID})['ads_qty']
        prefs = {'ads_qty': ads_qty, 'charting_tool': charting_tool}

        if request.method == 'POST':
            prefsform = Preferences(request.form)
            if prefsform.validate():
                # save updated data to db:
                # check for data to be updated
                datatoupdate = {}
                ads_qty_flag, charting_tool_flag = False, False
                if ads_qty != int(prefsform.ads_qty.data):
                    ads_qty_flag = True
                    datatoupdate['ads_qty'] = prefsform.ads_qty.data
                if charting_tool != prefsform.charting_tool.data:
                    charting_tool_flag = True
                    datatoupdate['charting_tool'] = prefsform.charting_tool.data
                # flash(str(datatoupdate))  # temp
                if ads_qty_flag or charting_tool_flag:
                    # flash('Updating DB') # temp
                    users.update_one({'_id': docID},
                                     {'$set': datatoupdate})
                    flash(
                        'Preferences successfully updated. Go to the <a href="/">main page</a> and choose some car model to try them.',
                        'alert alert-success')
            return render_template('preferences.html', prefsform=prefsform)

        # GET request
        prefsform = Preferences(data=prefs)
        return render_template('preferences.html', prefsform=prefsform)

    except Exception as e:
        # 2be removed in final version
        #flash(e, 'alert alert-danger')
        return redirect(url_for('index'))

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html')

# Run Flask server (host='0.0.0.0' - for Vagrant)
if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)
# hello
