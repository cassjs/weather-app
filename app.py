import requests
from flask import Flask, render_template

app = Flask(__name__)

app.config['DEBUG'] = True

@app.route('/')
def index():
    url = 'http://api.openweathermap.org/data/2.5/weather?q={}&units=imperial&appid='
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