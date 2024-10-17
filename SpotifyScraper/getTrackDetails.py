import requests
import json
import pprint
import time
import base64
import random
import os
from dotenv import load_dotenv
import re
from . import utils

load_dotenv()
global access_token
client_id = os.environ.get("CLIENT_ID_3")
client_secret = os.environ.get("CLIENT_SECRET_3")


def updateComposerTrackDetails():
    """
    Fetches details of all tracks in data/tracks
    """
    global access_token
    access_token = None
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Get all composers
    with open(os.path.join(script_dir, '../data/composers.json'), encoding='utf-8') as fp:
        composers = json.load(fp)
    composers = composers['composers']

    # Get all existing track details files
    files = os.listdir(os.path.join(script_dir, '../data/tracksDetails'))
    pattern = re.compile(r'tracksDetails_(.+)\.json')
    existingIds = [pattern.match(file).group(1) for file in files if pattern.match(file)]

    i = 0
    while i < len(composers):
        composerName = composers[i]['name']
        composerId = composers[i]['id']
        if composerId in existingIds:
            print(f'Skipping tracksDetails fetch of {composerName}')
            i = i + 1
        elif not os.path.exists(os.path.join(script_dir, f"../data/tracks/tracks_{composerId}.json")):
            print(f'Tracks of {composerName} not found. Skipping')
            i = i + 1
        else:
            print('------------------------------------------')
            print(f'Fetching track details of {composers[i]["name"]}')
            print('------------------------------------------')
            composerTracksDetails = getComposerTrackDetails(composerId)
            uniqueTracksDetails = list({ each['id'] : each for each in composerTracksDetails }.values())
            composerTracksDetailsJson = {'tracks': uniqueTracksDetails}
            with open(os.path.join(script_dir, f'../data/tracksDetails/tracksDetails_{composerId}.json'), 'w', encoding='utf-8') as f:
                json.dump(composerTracksDetailsJson, f, ensure_ascii=False)
            time.sleep(5 * (random.random() + 1))
            i = i + 1

def getComposerTrackDetails(artistId):
    """
    Fetches details of all tracks from given composer
    
    Returns:
        list[object]: list with objects with name and id of track, composer, other artists, and popularity
    """

    global access_token
    script_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(script_dir, f"../data/tracks/tracks_{artistId}.json"), encoding='utf-8') as fp:
        tracks = json.load(fp)
    tracks = tracks['tracks']
    composerTracksDetails = []

    chunkSize = 50
    url = 'https://api.spotify.com/v1/tracks?'
    j = 0
    while j < len(tracks):
        time.sleep(1 * (random.random() + 1))

        print(f"Getting tracks {j} to {j + chunkSize} from {artistId}")
        tracksList = tracks[j:j + chunkSize]
        tracksStr = ','.join(tracksList)
        fetch_url = f"{url}ids={tracksStr}"
        response = requests.get(fetch_url, headers={'Authorization': f'Bearer {access_token}'})

        # If not authorized, get new token
        if response.status_code == 401:
            print(f'Reponse 401. Getting new token')
            access_token = utils.getNewToken(client_id, client_secret)

        # If over-request, wait and retry afterwards
        elif response.status_code == 429:
            retryAfter = response.headers.get('retry-after')
            print(f'Response 429. Sleeping for {retryAfter} seconds')
            time.sleep(int(retryAfter))

        elif response.status_code == 200:
            responseJson = response.json()
            items = responseJson['tracks']
            for i in range(len(items)):
                trackArtistNames = []
                for k in range(len(items[i]['artists'])):
                    trackArtistNames.append(items[i]['artists'][k]['name'])
                composerTracksDetails.append({'name': items[i]['name'],
                                              'id': items[i]['id'],
                                              'composer': trackArtistNames[0],
                                              'artists': trackArtistNames[1:],
                                              'popularity': items[i]['popularity']})
            j = j + chunkSize

        else:
            print(response.json())
            print('Bad response, trying again')

    return composerTracksDetails
