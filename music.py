from flask import Flask, request, redirect, render_template
import requests
from dotenv import dotenv_values
import json
import time
import jinja2

class MyData:
    def __init__(self):
        self.history = []
        self.access_token = ""
        self.artist_freq = {}
        self.genre_freq = {}
        self.name = ""

    def process_results(self):
        x1 = time.time()
        for song in self.history:
            artist_id = song['artist']['id']
            album_id = song['album']['id']
            if artist_id in self.artist_freq:
                self.artist_freq[artist_id] += 1
            else:
                self.artist_freq[artist_id] = 1

            url = f'https://api.deezer.com/album/{album_id}?access_token={data.access_token}'
            res_data = requests.get(url).json()
            if 'genres' in res_data and 'data' in res_data['genres']:
                for genre in res_data['genres']['data']:
                    genre_name = genre['id']
                    if genre_name in self.genre_freq:
                        self.genre_freq[genre_name] += 1
                    else:
                        self.genre_freq[genre_name] = 1
        x2 = time.time()
        print("time taken to process results: ", x2 - x1)
    
    def fetch_results(self):
        if len(self.artist_freq) == 0 or len(self.genre_freq) == 0:
            self.process_results()
        return self.artist_freq, self.genre_freq


app = Flask(__name__)
data = MyData()  # Create a shared state object

config = dotenv_values(".env")

DEEZER_APP_ID = config["DEEZER_APP_ID"]
DEEZER_APP_SECRET = config["DEEZER_APP_SECRET"]
DEEZER_REDIRECT_URI = "http://127.0.0.1:5000/deezer/login"

@app.route('/', methods=['GET'])
def default():
    url = (f'https://connect.deezer.com/oauth/auth.php?app_id={DEEZER_APP_ID}'
           f'&redirect_uri={DEEZER_REDIRECT_URI}&perms=basic_access,email,listening_history')
    return redirect(url)

@app.route('/deezer/login', methods=['GET'])
def deezer_login():
    code = request.args.get('code')

    url = (f'https://connect.deezer.com/oauth/access_token.php?app_id={DEEZER_APP_ID}'
           f'&secret={DEEZER_APP_SECRET}&code={code}&output=json')
    response = requests.get(url)
    
    if response.text == 'wrong code':
        return 'wrong code'
    
    data.access_token = response.json()['access_token']
    
    url = f'https://api.deezer.com/user/me/tracks?access_token={data.access_token}'
    res_data = requests.get(url).json()
    data.history = res_data['data']
    i = 1
    while len(res_data['data']) != 0:
        url = f'https://api.deezer.com/user/me/tracks?access_token={data.access_token}&index={i * 25}'
        res_data = requests.get(url).json()
        if 'data' in res_data:
            print("Received ", len(res_data['data']), " items")
            data.history += res_data['data']
            i += 1
    """ with open("history_json", 'w') as f:
        json.dump(data.history, f) """
    print("length of history: ", len(data.history))
    return redirect("/results")

@app.route('/results')
def results():
    artist_freq, genre_freq = data.fetch_results()
    url = f'https://api.deezer.com/user/me/name?access_token={data.access_token}'
    res_data = requests.get(url).json()
    name = res_data['name']
    return render_template('results.html', artist_freq=artist_freq, genre_freq=genre_freq, name=name)

if __name__ == '__main__':
    app.run()
