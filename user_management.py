import os
import imghdr
from flask import Flask, request, render_template, url_for, redirect, session, flash
from wtforms import Form, StringField, PasswordField, SubmitField, SelectField, TextAreaField, FileField
from wtforms.validators import Length, DataRequired, Email, EqualTo
from flask_bootstrap import Bootstrap
from pymongo import MongoClient
from passlib.hash import sha256_crypt
from functools import wraps
from flask_mail import Mail, Message
import string, random


app = Flask(__name__)
bootstrap = Bootstrap(app)
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

mail = Mail(app)
app.config.update(
    DEBUG=True,
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_SSL=False,
    MAIL_USE_TLS=True,
    MAIL_USERNAME = 'mailvulgaris@gmail.com',
    MAIL_PASSWORD = 'flaskflask'
)
# ! need to reinitialize!
mail = Mail(app)

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
        if 'logged_in' not in session:
            return f(*args, **kwargs)
        else:
            flash('You need to log out first', 'alert alert-warning')
            return redirect(url_for('login'))
    return wrap

@app.route('/')
def index():
    try:
        if not session:
            flash('Hello. This is an index page. <a href="/login">Login</a> or <a href="/register">register</a>.',
                  'alert alert-primary')
        else:
            flash('Hello, ' + session[
                'user'] + '. You are logged in. Go to <a href="/profile">profile</a> or <a href="/logout">logout</a>',
                  'alert alert-primary')
    except Exception as e:
        pass
    return render_template('hello.html')

@app.route('/register/', methods=['GET', 'POST'])
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
            if users.find_one({'username': username}) or users.find_one({'email': email}):
                flash('Sorry, but this username or email are already taken. Please choose different credentials or <a href="/login">login</a>', 'alert alert-warning')
                return render_template('register.html', form=form)
            else:
                users.insert_one({'username': username, 'email': email, 'password': password, 'status': 'active', 'language': 'en', 'description': '', 'avatar': 'default.jpg'})
                session['logged_in'] = True
                session['username'] = username
                flash('Registration successfull! <a href="/logout/">Logout</a> or go to your <a href="/profile">profile</a>', 'alert alert-success')
                return redirect(url_for('index'))

        # the first (GET) request for a registration form
        return render_template('register.html', form=form)

    except Exception as e:
        # 2be removed in final version
        flash(e, 'alert alert-danger')
        return redirect(url_for('index'))

@app.route('/login/', methods=['GET', 'POST'])
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

            # let's check for this login in usernames or emails
            docID = None
            username = ''
            if users.find_one({'username': usernameoremail}):
                docID = users.find_one({'username': usernameoremail}).get('_id')
                username = usernameoremail
            elif users.find_one({'email': usernameoremail}):
                docID = users.find_one({'email': usernameoremail}).get('_id')
                username = users.find_one({'_id': docID})['username']
            else:
                flash('Sorry, we do not recognize this username or email address. Please choose different credentials or <a href="/register/">register</a>', 'alert alert-warning')
                return render_template('login.html', loginform=loginform)

            # and then let's check for a password
            pwd_should_be = users.find_one({'_id': docID})['password']
            if sha256_crypt.verify(password, pwd_should_be):
                session['logged_in'] = True
                session['username'] = username
                flash('Login successfull! <a href="/logout/">Logout</a> or go to <a href="/profile">profile</a>', 'alert alert-success')
                return redirect(url_for('index'))
            # invalid password
            else:
                flash('Wrong password', 'alert alert-danger')
                return render_template('login.html', loginform=loginform)

        # the first (GET) request for a login form
        return render_template('login.html', loginform=loginform)

    except Exception as e:
        # 2be removed in final version
        flash(e, 'alert alert-danger')
        return redirect(url_for('index'))

@app.route('/logout/')
@login_required
def logout():
    session.clear()
    flash('You have been logged out. <a href="/login">Login</a> again or <a href="/register">register</a> another user', 'alert alert-success')
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

        username = session['username'] # getting username from session variable (to determine document's ID)
        docID = users.find_one({'username': username}).get('_id')
        email = users.find_one({'_id': docID})['email']
        lang = users.find_one({'_id': docID})['language']
        description = users.find_one({'_id': docID})['description']
        #flash(str(docID)) # temp
        person = {'username': username, 'email': email, 'language': lang, 'description': description}
        #flash(str(person))  # temp

        if request.method == 'POST':
            profileform = ProfileForm(request.form)
            if profileform.validate():
                # save updated data to db
                # check for data to be updated
                #flash('POST request ok')  # temp
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
                #flash(str(datatoupdate))  # temp
                if userflag or emailflag or langflag or descrflag:
                    #flash('Updating DB') # temp
                    users.update_one({'_id': docID},
                                                  {'$set': datatoupdate})
                    flash('Profile successfully updated. Now you can go to <a href="/">index page</a> or <a href="/logout">logout</a>.', 'alert alert-success')
            return render_template('profile.html', profileform=profileform)

        # GET request
        profileform = ProfileForm(data=person)
        return render_template('profile.html', profileform=profileform)

    except Exception as e:
        # 2be removed in final version
        flash(e, 'alert alert-danger')
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
        image = '../static/uploads/' + users.find_one({'_id': docID})['avatar']
        #flash(image) # temp
        #flash(str(docID)) # temp

        avatarform = UploadForm()

        if request.method == 'POST':#and avatarform.validate():
            #flash('Filename: ' + request.files['image_file'].filename) # temp
            if request.files['image_file'].filename[-4:].lower() != '.jpg':
                flash('Invalid file extension. Only .jpg/.jpeg images allowed',
                            'alert alert-warning')
                return render_template('avatar.html', avatarform=avatarform, image=image)
            if imghdr.what(request.files['image_file']) != 'jpeg':
                flash('Invalid image format. Are you sure that\'s really a .jpeg image? Please choose a different one',
                            'alert alert-warning')
                return render_template('avatar.html', avatarform=avatarform, image=image)

            path = 'uploads/' + str(docID) + '.jpg'
            request.files['image_file'].save(os.path.join(app.static_folder, path))
            users.update_one({'_id': docID}, {'$set': {'avatar': str(docID)+'.jpg'}})
            # avoid image caching
            image = '../static/uploads/' + str(docID) + '.jpg' + '?' + str(random.randint(1,10000))
            #flash(image) # temp
        return render_template('avatar.html', avatarform=avatarform, image=image)

        # GET request
        return render_template('avatar.html', avatarform=avatarform, image=image)

    except Exception as e:
        # 2be removed in final version
        flash(e, 'alert alert-danger')
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
                #flash(newpassword) # temp

                # and send it to user
                msg = Message('You new password', sender="from@example.com", recipients=[newemail])
                msg.html = 'Here\'s your new password: ' + newpassword + '<br> You can change it using <a href="#">password update</a> form'
                mail.send(msg)
                # and also update it in our DB
                users.update_one({'email': newemail}, {'$set': {'password': sha256_crypt.encrypt(newpassword)}})
                flash('Password successfully updated! Please check your inbox. You can change this password using the <a href="#">password update</a> form',
                    'alert alert-success')
            return redirect(url_for('index'))

        # GET request
        return render_template('password_reset.html', pwdresetform=pwdresetform)

    except Exception as e:
        # 2be removed in final version
        flash(e, 'alert alert-danger')
    return redirect(url_for('index'))

# Run Flask server (host='0.0.0.0' - for Vagrant)
if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)