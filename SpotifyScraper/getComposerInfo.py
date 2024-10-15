import requests
import json
import pprint
import time
import base64
import random
import os
from . import utils
from dotenv import load_dotenv

load_dotenv()
client_id = os.environ.get("CLIENT_ID")
client_secret = os.environ.get("CLIENT_SECRET")

def updateComposerInfo():
    """
    Gets the composer IDs and official name in Spotify

    Needs composers.json file in data folder
    """

    access_token = None
    script_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(script_dir, '../data/composers.json'), encoding='utf-8') as fp:
        composers = json.load(fp)
    composers = composers['composers']
    i = 0
    while i < len(composers):
        print(f'Fetching ID of {composers[i]["name"]}')
        url = f"https://api.spotify.com/v1/search/?q={composers[i]['name']}&type=artist"
        response = requests.get(url, headers={'Authorization': f'Bearer {access_token}'})

        # If response OK, update name and id of composer
        if response.status_code == 200:
            responseJson = response.json()
            composerFound = responseJson['artists']['items'][0]
            composers[i]['name'] = composerFound['name']
            composers[i]['id'] = composerFound['id']
            i = i + 1
            time.sleep(2)

        # If unauthorized, re-authenticate and request again
        elif response.status_code == 401:
            print(f'Reponse 401. Getting new token')
            access_token = utils.getNewToken(client_id, client_secret)

        # If over-request, wait and retry afterwards
        elif response.status_code == 429:
            retryAfter = response.headers.get('retry-after')
            print(f'Response 429. Sleeping for {retryAfter} seconds')
            time.sleep(int(retryAfter))

        else:
            raise RuntimeError('Bad Request. Halting code')

    uniqueComposers = list({ each['name'] : each for each in composers }.values())
    composersJson = {'composers': uniqueComposers}
    with open(os.path.join(script_dir, '../data/composers.json'), 'w', encoding='utf-8') as f:
        json.dump(composersJson, f, ensure_ascii=False)
