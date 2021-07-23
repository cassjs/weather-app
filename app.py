import requests
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy 

app = Flask(__name__)

### DATABASE ###
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weatherdb.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cityname = db.Column(db.String(50), nullable=False)
    
db.create_all()

### ROUTES ###
@app.route('/')
def index():
    # Create variable to hold ALL cities
    cities = City.query.all()
    
    # Open Weather API: https://openweathermap.org/
    url = 'http://api.openweathermap.org/data/2.5/weather?q={}&units=imperial&appid='

    # List that holds weather for all cities
    weather_data = []
    
    # For each city in loop, send a request to api to fetch data, then place data in dictionary
    for city in cities:
        
        # send request to api
        r = requests.get(url.format(city.cityname)).json()
        
        # create dictionary
        weather = {
            'city' : city.cityname,
            'temperature' : r['main']['temp'],
            'description' : r['weather'][0]['description'],
            'icon' : r['weather'][0]['icon'],
            'high' : r['main']['temp_max'],
            'low' : r['main']['temp_min']
        }
        
        # After every loop, append weather for city to weather_data list
        weather_data.append(weather)
    
    return render_template('base.html', weather_data=weather_data)

if __name__ == '__main__':
    app.run(debug=True)