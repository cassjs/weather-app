import requests
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy 
from dotenv import load_dotenv
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weatherdb.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# To use msg flashing, need secret key
app.config['SECRET_KEY'] = 'secret'

db = SQLAlchemy(app)

class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cityname = db.Column(db.String(50), nullable=False)
    
db.create_all()

def get_weather_data(city):
    load_dotenv()
    API_KEY = os.getenv("API_KEY")
    # Open Weather API: https://openweathermap.org/
    url = f'http://api.openweathermap.org/data/2.5/weather?q={ city }&units=imperial&appid={ API_KEY }'
    r = requests.get(url).json()
    return r

@app.route('/', methods=['GET'])
def index():
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
    
    return render_template('base.html', weather_data=weather_data)

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
    
    return redirect(url_for('index'))

@app.route('/delete/<cityname>')
def delete(cityname):
    city = City.query.filter_by(cityname=cityname).first()
    db.session.delete(city)
    db.session.commit()
    
    flash(f'Successfully deleted { city.cityname }', 'alert-success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=False)