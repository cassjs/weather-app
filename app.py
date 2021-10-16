from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from twilio.rest import Client
from dotenv import load_dotenv
from flask_bootstrap import Bootstrap
import requests
import os

app = Flask(__name__)

# Load enviornment variables
load_dotenv()

# Twilio Private keys hidden locally only via .env file
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN= os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_VERIFY_SERVICE = os.environ.get('TWILIO_VERIFY_SERVICE')
SENDGRID_API_KEY= os.environ.get('SENDGRID_API_KEY') 

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weatherdb.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secret'

bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# City DB table
class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cityname = db.Column(db.String(50), nullable=False)

# User DB table    
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))
    
db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')

class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])

def get_weather_data(city):
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
    # Open Weather API: https://openweathermap.org/
    url = f'http://api.openweathermap.org/data/2.5/weather?q={ city }&units=imperial&appid={ OPENWEATHER_API_KEY }'
    r = requests.get(url).json()
    return r

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard', methods=['GET'])
def dashboard():
    # Create variable to hold ALL cities
    cities = City.query.all()

    # List that holds weather for all cities
    weather_data = []
    
    # For each city in loop, send a request to api to fetch data, then place data in dictionary
    for city in cities:
        
        r = get_weather_data(city.cityname)
        # # view data returned from api
        # print(r)
        
        # create dictionary
        weather = {
            'city' : city.cityname,
            'country' : r['sys']['country'],
            'temperature' : r['main']['temp'],
            'description' : r['weather'][0]['description'],
            'icon' : r['weather'][0]['icon'],
            'high' : r['main']['temp_max'],
            'low' : r['main']['temp_min']
        }
        
        # After every loop, append weather for city to weather_data list
        weather_data.append(weather)
    
    return render_template('dashboard.html', weather_data=weather_data, name=current_user.username)

@app.route('/add/', methods=['POST'])
def add():
    error_msg = ''
    newcity = request.form.get('city')
    
    if newcity:
        # Check if city is already in database
        cityexists = City.query.filter_by(cityname=newcity).first()
        
        if not cityexists:
            newcity_data = get_weather_data(newcity)
            # Check if city is a valid entry
            if newcity_data['cod'] == 200:
                newcity_obj = City(cityname=newcity)
                
                # Add city to database if valid or does not exist in database
                db.session.add(newcity_obj)
                db.session.commit()
            else:
                error_msg = 'City is invalid.'
                # print(error_msg)
        else:
            error_msg = 'City already exists. Try again.'
            # print(error_msg)
            
    if error_msg: 
        flash(error_msg, 'error')
    else: 
        flash('City added successfully.')
    
    return redirect(url_for('dashboard'))

@app.route('/delete/<cityname>')
def delete(cityname):
    city = City.query.filter_by(cityname=cityname).first()
    db.session.delete(city)
    db.session.commit()
    
    flash(f'Successfully deleted { city.cityname }', 'alert-success')
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                # flash('Welcome {{ name }}')
                return redirect(url_for('dashboard'))
            else:
                print("Authentication failed. Invalid username or password. Try again.")
                return render_template('login.html')
    return render_template('login.html', form=form, username=form.username.data)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

    if request.method == 'POST':
        to_email = request.form['email']
        session['to_email'] = to_email
        send_verification(to_email)
        return redirect(url_for('generate_verification_code'))
    return render_template('signup.html', form=form)

# Twilio client sends verification code to the user's email
def send_verification(to_email):
    verification = client.verify \
        .services(TWILIO_VERIFY_SERVICE) \
        .verifications \
        .create(to=to_email, channel='email')
    print(verification.sid)
        
@app.route('/verificationcode', methods=['GET', 'POST'])
# The verify page is rendered. 
# If verification code is correct, a success message is returned
# Else, if verification code is invalid, try again error will appear
def generate_verification_code():
    to_email = session['to_email']
    error = None
    if request.method == 'POST':
        verification_code = request.form['verificationcode']
        if check_verification_token(to_email, verification_code):
            return redirect(url_for('login'))
        else:
            error = "Invalid verification code. Try again."
            return render_template('verifycode.html', error = error)
    return render_template('verifycode.html', email = to_email)

# Takes email and the verification code entered by user, then calls the Verify API to check code provided back by user
def check_verification_token(phone, token):
    check = client.verify \
        .services(TWILIO_VERIFY_SERVICE) \
        .verification_checks \
        .create(to=phone, code=token)    
    return check.status == 'approved'

if __name__ == '__main__':
    app.run(debug=False)