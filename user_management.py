from flask import Flask, request, render_template, url_for, redirect, session, flash
from wtforms import Form, StringField, PasswordField, SubmitField, validators
from flask_bootstrap import Bootstrap
from pymongo import MongoClient
from passlib.hash import sha256_crypt

app = Flask(__name__)
bootstrap = Bootstrap(app)
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

class RegistrationForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=20)])
    email = StringField('Email Address', [validators.Length(min=6, max=50),validators.DataRequired(), validators.Email()])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')

class LoginForm(Form):
    usernameoremail = StringField('Username or Email Address', [validators.DataRequired()])
    password = PasswordField('Password', [validators.DataRequired()])

@app.route('/')
def index():
    flash('Index page (direct request). <a href="/register/">Register</a> or <a href="/login/">login</a>', 'alert alert-primary')
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
                flash('Sorry, but this username or email are already taken. Please choose different credentials', 'alert alert-warning')
                return render_template('register.html', form=form)
            else:
                users.insert_one({'username': username, 'email': email, 'password': password, 'status': 'active'})
                session['logged in'] = True
                session['username'] = username
                flash('Registration successfull! <a href="#">Logout</a> or <a href="/">back to main page</a>', 'alert alert-success')
                return render_template('hello.html')

        # the first (GET) request for a registration form
        return render_template('register.html', form=form)

    except Exception as e:
        # 2be removed in final version
        flash(e, 'alert alert-danger')
        return render_template('hello.html')

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
                session['logged in'] = True
                session['username'] = username
                flash('Login successfull! <a href="#">Logout</a> or <a href="/">back to main page</a>', 'alert alert-success')
                return render_template('hello.html')
            # invalid password
            else:
                flash('Wrong password', 'alert alert-danger')
                return render_template('login.html', loginform=loginform)

        # the first (GET) request for a login form
        return render_template('login.html', loginform=loginform)

    except Exception as e:
        # 2be removed in final version
        flash(e, 'alert alert-danger')
        return render_template('hello.html')


# Run Flask server (host='0.0.0.0' - for Vagrant)
if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)