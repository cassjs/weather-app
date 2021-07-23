import requests
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy 

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weatherdb.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cityname = db.Column(db.String(50), nullable=False)
    
db.create_all()

@app.route('/')
def index():
    url = 'http://api.openweathermap.org/data/2.5/weather?q={}&units=imperial&appid=734bd3e5ad848030de098b13791517e1'
    city = 'Beaverton'
    
    r = requests.get(url.format(city)).json()
    print(r)
    
    # dictionary
    weather = {
        'city' : city,
        'temperature' : r['main']['temp'],
        'description' : r['weather'][0]['description'],
        'icon' : r['weather'][0]['icon'],
        'high' : r['main']['temp_max'],
        'low' : r['main']['temp_min']
    }
    
    print(weather)
    
    return render_template('base.html', weather=weather)


if __name__ == '__main__':
    app.run(debug=True)