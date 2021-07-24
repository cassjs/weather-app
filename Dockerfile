FROM python:3.8-buster

WORKDIR /weather-app

# Copy file and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt 

# Copy required files
COPY . .

# Run Application
ENTRYPOINT FLASK_APP=app.py flask run --host=0.0.0.0