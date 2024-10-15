import requests
import json
import pprint
import time
import base64
from config import *
import random

client_id = CLIENT_ID_1
client_secret = CLIENT_SECRET_1
access_token = ACTOKEN_1
refresh_token = RFTOKEN_1


def updateComposerTrackDetails():
    with open(r'C:\Users\leonardo.calasans\Desktop\MusicPearls\data\composers.json', encoding='utf-8') as fp:
        composers = json.load(fp)
    composers = composers['composers']

    for i in range(11, 12):
        print('------------------------------------------')
        print(f'Fetching track details of {composers[i]["name"]}')
        print('------------------------------------------')

        composerTracksDetails = getComposerTrackDetails(composers[i]["id"])
        composerTracksDetailsJson = {'tracks': composerTracksDetails}

        with open(f'tracksDetails2/tracksDetails_{composers[i]["id"]}.json', 'w', encoding='utf-8') as f:
            json.dump(composerTracksDetailsJson, f, ensure_ascii=False)
        time.sleep(5 * (random.random() + 1))


def getComposerTrackDetails(artistId):
    # Open track id file and get all ids of tracks
    with open(fr'C:\Users\leonardo.calasans\Desktop\MusicPearls\data\tracks2\tracks_{artistId}.json',
              encoding='utf-8') as fp:
        tracks = json.load(fp)
    tracks = tracks['tracks']

    # Initialize variables
    composerTracksDetails = []
    chunkSize = 50
    global access_token
    url = 'https://api.spotify.com/v1/tracks?'

    # Loop through all tracks getting their details
    j = 0
    while j < len(tracks):
        time.sleep(1 * (random.random() + 1))

        print(f"Getting tracks {j} to {j + chunkSize}")
        tracksList = tracks[j:j + chunkSize]
        tracksStr = ','.join(tracksList)
        fetch_url = f"{url}ids={tracksStr}"
        response = requests.get(fetch_url, headers={'Authorization': f'Bearer {access_token}'})

        # If not authorized, get new token
        if response.status_code == 401:
            print(f'Reponse 401. Getting new token')
            access_token = getNewToken()

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


def getNewToken():
    url = 'https://accounts.spotify.com/api/token'
    auth_client = client_id + ":" + client_secret
    auth_encode = 'Basic ' + base64.b64encode(auth_client.encode()).decode()
    response = requests.post(url,
                             headers={'Content-Type': 'application/x-www-form-urlencoded',
                                      'Authorization': auth_encode},
                             data={'grant_type': 'refresh_token', 'refresh_token': refresh_token})
    if response.status_code == 200:
        responseJson = response.json()
        return responseJson['access_token']
    else:
        raise RuntimeError('Unable to refresh Access Token')


updateComposerTrackDetails()
