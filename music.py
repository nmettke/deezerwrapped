from flask import Flask, request, redirect
import requests
from dotenv import dotenv_values
import json
import time


app = Flask(__name__)

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
    
    access_token = response.json()['access_token']
    
    history = []
    for i in range(20):
        url = f'https://api.deezer.com/user/me/history?access_token={access_token}&index={i * 50}'
        response = requests.get(url)
        data = response.json()
        if 'data' in data:
            print("Received ", len(data['data']), " items")
            history += data['data']
        time.sleep(.5)
    with open("history_json", 'w') as f:
        json.dump(history, f)
    print("length of history: ", len(history))
    return history

if __name__ == '__main__':
    app.run()