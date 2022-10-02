from flask import Flask, render_template, request, make_response, session
import requests
import json
from urllib.parse import urlparse, urljoin
from flask import Flask, request, render_template, redirect, url_for, flash, abort
from flask_login import (LoginManager, current_user, login_required,
                         login_user, logout_user, UserMixin,
                         confirm_login, fresh_login_required)
from flask_wtf import FlaskForm as Form
from wtforms import BooleanField, StringField, validators
from passlib.hash import sha256_crypt as pwd_context
import os

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

backAddr = os.environ['BACKEND_ADDR']
backPort = os.environ['BACKEND_PORT']

# """
# Flask-Login and Flask-WTF example
# """

def hash_password(password):
    return pwd_context.using(salt="abcdefg").hash(password)

class LoginForm(Form):
    username = StringField('Username', [validators.Length(min=1, max=25,message=u"Huh, little too short for a username."),
                                        validators.InputRequired(u"Please enter a username")])
    password = StringField('Password',[validators.Length(min=1,message=u"Huh, little too short for a password."),
                                       validators.InputRequired(u"Please enter a password.")])
    remember = BooleanField('Remember me')

class RegisterForm(Form):
    username = StringField('Username', [validators.Length(min=1, max=25,message=u"Huh, little too short for a username."),
                                        validators.InputRequired(u"Please enter a username")])
    password = StringField('Password',[validators.Length(min=1,message=u"Huh, little too short for a password."),
                                       validators.InputRequired(u"Please enter a password.")])

def is_safe_url(target):
    """
    :source: https://github.com/fengsp/flask-snippets/blob/master/security/redirect_back.py
    """
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


class User(UserMixin):
    def __init__(self, id, name, token = None):
        self.id = id
        self.name = name
        self.token = token
    def get_id(self):
        return self.id

app = Flask(__name__)
app.secret_key = "and the cats in the cradle and the silver spoon"

app.config.from_object(__name__)

login_manager = LoginManager()

login_manager.session_protection = "basic"

login_manager.login_view = "login"
login_manager.login_message = u"Please log in to access this page."

login_manager.refresh_view = "login"
login_manager.needs_refresh_message = (
    u"To protect your account, please reauthenticate to access this page."
)
login_manager.needs_refresh_message_category = "info"


@login_manager.user_loader
def load_user(id):
    if not 'id' in session:
        return None
    return User(id, session['username'],session['token'])

login_manager.init_app(app)


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit() and request.method == "POST" and "username" in request.form:
        username = request.form["username"]
        password = hash_password(request.form["password"])
        loginStuff = requests.get(f'http://{backAddr}:{backPort}/token?username={username}&password={password}')
        if loginStuff.status_code == 200:
            remember = request.form.get("remember", "false") == "true"
            userDetails = json.loads(loginStuff.content)
            token = userDetails['token']
            id = userDetails['id']
            session['username'] = username
            session['token'] = token
            session['id'] = id
            login_user(User(id,username,token), remember=remember)
            flash("Logged in!")
            flash("I'll remember you") if remember else None
            next = request.args.get("next")
            if not is_safe_url(next):
                abort(400)
            return redirect(next or url_for('index'))
        else:
            flash((loginStuff.text))
    return render_template("login.html", form=form)

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit() and request.method == "POST" and "username" in request.form:
        username = request.form["username"]
        password = hash_password(request.form["password"])
        obj = {'username':username, 'password':password}
        registerStuff = requests.post(f'http://{backAddr}:{backPort}/register', obj)
        if registerStuff.status_code == 201:
            flash("Registered! Now please log in.")
            next = request.args.get("next")
            if not is_safe_url(next):
                abort(400)
            return redirect(next or url_for('login'))
        else:
            flash(registerStuff.text)
    return render_template("register.html", form=form)

@app.route('/listall')
@app.route('/listall/')
@app.route('/listall/<string:format>')
@login_required
def listAll(format = None):
    k = request.args.get('top', default=-1, type=int)
    if k <= -1:
        k = None
    if format == None:
        format = 'json'
    else:
        format = format.lower()
    if requests.get(f'http://{backAddr}:{backPort}/listAll').text.strip() == '{}':
        return render_template('index.html', stuff = "The database is empty")
    if format == 'csv':
        r = requests.get(f'http://{backAddr}:{backPort}/listAll/csv?top='+str(k)+"&token="+str(session['token']))
        if r.status_code == 401:
            flash(r.text)
            logout_user()
            return render_template('index.html')
        b = r.text.replace('\\n','<br>')
        return render_template('index.html', stuff = b[1:-2])
    if format == 'json':
        r = requests.get(f'http://{backAddr}:{backPort}/listAll/json?top='+str(k)+"&token="+str(session['token']))
        if r.status_code == 401:
            flash(r.text)
            logout_user()
            return render_template('index.html')
        r = r.text
        return render_template('index.html', stuff = r)

@app.route('/listclose')
@app.route('/listclose/')
@app.route('/listclose/<string:format>')
@login_required
def listclose(format = None):
    k = request.args.get('top', default=-1, type=int)
    if k <= -1:
        k = None
    if format == None:
        format = 'json'
    else:
        format = format.lower()
    if requests.get(f'http://{backAddr}:{backPort}/listAll').text.strip() == '{}':
        return render_template('index.html', stuff = "The database is empty")
    if format == 'csv':
        r = requests.get(f'http://{backAddr}:{backPort}/listCloseOnly/csv?top='+str(k)+"&token="+str(session['token']))
        if r.status_code == 401:
            flash(r.text)
            logout_user()
            return render_template('index.html')
        b = r.text.replace('\\n','<br>')
        return render_template('index.html', stuff = b[1:-2])
    if format == 'json':
        r = requests.get(f'http://{backAddr}:{backPort}/listCloseOnly/json?top='+str(k)+"&token="+str(session['token']))
        if r.status_code == 401:
            flash(r.text)
            logout_user()
            return render_template('index.html')
        r = r.text
        return render_template('index.html', stuff = r)

@app.route('/listopen')
@app.route('/listopen/')
@app.route('/listopen/<string:format>')
@login_required
def listOpen(format = None):
    k = request.args.get('top', default=-1, type=int)
    if k <= -1:
        k = None
    if format == None:
        format = 'json'
    else:
        format = format.lower()
    if requests.get(f'http://{backAddr}:{backPort}/listAll').text.strip() == '{}':
        return render_template('index.html', stuff = "The database is empty")
    if format == 'csv':
        r = requests.get(f'http://{backAddr}:{backPort}/listOpenOnly/csv?top='+str(k)+"&token="+str(session['token']))
        if r.status_code == 401:
            flash(r.text)
            logout_user()
            return render_template('index.html')
        b = r.text.replace('\\n','<br>')
        return render_template('index.html', stuff = b[1:-2])
    if format == 'json':
        r = requests.get(f'http://{backAddr}:{backPort}/listOpenOnly/json?top='+str(k)+"&token="+str(session['token']))
        if r.status_code == 401:
            flash(r.text)
            logout_user()
            return render_template('index.html')
        r = r.text
        return render_template('index.html', stuff = r)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    for key in list(session.keys()):
        session.pop(key)
    flash("Logged out.")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')