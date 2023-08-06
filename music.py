from flask import Flask, request, redirect, render_template
import requests
from dotenv import dotenv_values
import json
import time
import jinja2
import os

class MyData:
    def __init__(self):
        self.history = []
        self.access_token = ""
        self.artist_freq = {}
        self.genre_freq = {}
        self.name = ""
        self.artist_sorted = []
        self.genre_sorted = []

    def process_results(self):
        x1 = time.time()
        for song in self.history:
            artist_id = song['artist']['id']
            artist_name = song['artist']['name']
            artist_picture = song['artist'].get("picture_big", "https://via.placeholder.com/500")
            artist_tuple = (artist_id, artist_name, artist_picture)
            if artist_tuple in self.artist_freq:
                self.artist_freq[artist_tuple] += 1
            else:
                self.artist_freq[artist_tuple] = 1
            
            album_id = song['album']['id']
            url = f'https://api.deezer.com/album/{album_id}?access_token={data.access_token}'
            res_data = requests.get(url).json()
            if 'genres' in res_data and 'data' in res_data['genres']:
                for genre in res_data['genres']['data']:
                    genre_id = genre['id']
                    genre_name = genre['name']
                    genre_picture = genre.get("picture", "https://via.placeholder.com/500")
                    genre_tuple = (genre_id, genre_name, genre_picture)
                    if genre_tuple in self.genre_freq:
                        self.genre_freq[genre_tuple] += 1
                    else:
                        self.genre_freq[genre_tuple] = 1
        x2 = time.time()

        self.artist_sorted = sorted(self.artist_freq.items(), key=lambda x:x[1], reverse=True)
        self.genre_sorted = sorted(self.genre_freq.items(), key=lambda x:x[1], reverse=True)

        print("time taken to process results: ", x2 - x1)
    
    def fetch_results(self):
        filename = 'data.json'
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
                self.artist_sorted = data['artist_sorted']
                self.genre_sorted = data['genre_sorted']
        else:
            self.process_results()
            data = {
                'artist_sorted': self.artist_sorted,
                'genre_sorted': self.genre_sorted,
            }
            with open(filename, 'w') as f:
                json.dump(data, f)

        return self.artist_sorted, self.genre_sorted


app = Flask(__name__)
data = MyData() 

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
    
    filename = 'history.json'
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            data.history = json.load(f)
    else:
        url = f'https://api.deezer.com/user/me/tracks?access_token={data.access_token}'
        res_data = requests.get(url).json()
        data.history = res_data['data']
        i = 1
        while len(res_data['data']) != 0:
            url = f'https://api.deezer.com/user/me/tracks?access_token={data.access_token}&index={i * 25}'
            res_data = requests.get(url).json()
            if 'data' in res_data:
                data.history += res_data['data']
                i += 1
        with open(filename, 'w') as f:
            json.dump(data.history, f)

    return redirect("/results")

@app.template_filter('slice')
def slice_filter(s, start, end):
    return s[start:end]

@app.route('/results')
def results():
    artist_sorted, genre_sorted = data.fetch_results()
    url = f'https://api.deezer.com/user/me?access_token={data.access_token}'
    res_data = requests.get(url).json()
    name = res_data['name']
    return render_template('results.html', artist_sorted=artist_sorted, genre_sorted=genre_sorted, name=name)

if __name__ == '__main__':
    app.run()