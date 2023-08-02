from flask import Flask, request, redirect
import requests
from dotenv import dotenv_values
import json
import time


class MyData:
    def __init__(self):
        self.history = []
        self.access_token = ""
        self.artist_freq = {}
        self.genre_freq = {}

    def process_results(self):
        for song in self.history:
            name = song['artist']['name']
            if name in self.artist_freq:
                self.artist_freq[name] += 1
            else:
                self.artist_freq[name] = 1
        print(self.artist_freq)
        return self.artist_freq


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
    with open("history_json", 'w') as f:
        json.dump(data.history, f)
    print("length of history: ", len(data.history))
    return redirect("/results")

@app.route('/results')
def results():
    return data.process_results()

if __name__ == '__main__':
    app.run()
