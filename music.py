from flask import Flask, request, redirect
import requests
from dotenv import dotenv_values


app = Flask(__name__)

config = dotenv_values(".env")

print(config)

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
    # retrieve the authorization code given in the url
    code = request.args.get('code')

    # request the access token
    url = (f'https://connect.deezer.com/oauth/access_token.php?app_id={DEEZER_APP_ID}'
           f'&secret={DEEZER_APP_SECRET}&code={code}&output=json')
    response = requests.get(url)
    
    # If it's not a good code we will get this error
    if response.text == 'wrong code':
        return 'wrong code'
    
    # We have our access token
    access_token = response.json()['access_token']
    
    url = f'https://api.deezer.com/user/me/history?access_token={access_token}'
    response = requests.get(url)
    history = response.json()
    return history

if __name__ == '__main__':
    app.run()