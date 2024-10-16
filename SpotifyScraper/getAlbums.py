import requests
import json
import pprint
import time
import base64
import random
from . import utils
import os
from dotenv import load_dotenv
import re

load_dotenv()
global access_token
client_id = os.environ.get("CLIENT_ID")
client_secret = os.environ.get("CLIENT_SECRET")

def updateComposerAlbums():
    """
    Fetches the albums of all composers in composers.json
    """

    global access_token
    access_token = None
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Get all composers
    with open(os.path.join(script_dir, '../data/composers.json'), encoding='utf-8') as fp:
        composers = json.load(fp)
    composers = composers['composers']

    # Get all existing albums files
    files = os.listdir(os.path.join(script_dir, '../data/albums'))
    pattern = re.compile(r'albums_(.+)\.json')
    existingIds = [pattern.match(file).group(1) for file in files if pattern.match(file)]

    i = 0
    while i < len(composers):
        composerName = composers[i]['name']
        composerId = composers[i]['id']
        if composerId in existingIds:
            print(f'Skipping albums fetch of {composerName}')
            i = i + 1
        else:
            print(f'Fetching albums of {composerName}')
            composerAlbums = getAlbums(composerId)
            uniqueAlbums = list(set(composerAlbums))
            composerAlbumsJson = {'albums': uniqueAlbums}
            with open(os.path.join(script_dir, f'../data/albums/albums_{composerId}.json'), 'w', encoding='utf-8') as f:
                json.dump(composerAlbumsJson, f, ensure_ascii=False)
            time.sleep((1 + random.random()) * 5)
            i = i + 1

def getAlbums(artistId, url=''):
    """
    Fetches all the albums of a given composer

    Returns:
        list[str]: list with all albums ids
    """

    global access_token
    if not url:
        url = 'https://api.spotify.com/v1/artists/' + artistId + '/albums?limit=50'

    albumsList = []
    print(url)
    response = requests.get(url, headers={'Authorization': f'Bearer {access_token}'})

    if response.status_code == 200:
        responseJson = response.json()
        items = responseJson['items']
        for i in range(len(items)):
            albumsList.append(items[i]['id'])
        if responseJson['next']:
            time.sleep((1 + random.random()) * 2)
            albumsList = albumsList + getAlbums(artistId=artistId, url=responseJson['next'])

    # If unauthorized, re-authenticate and request again
    elif response.status_code == 401:
        print(f'Reponse 401. Getting new token')
        access_token = utils.getNewToken(client_id, client_secret)

        # Keep current albums alredy fetched and keep fetching
        albumsList = albumsList + getAlbums(artistId=artistId, url=url)

    # If over-request, wait and retry afterwards
    elif response.status_code == 429:
        retryAfter = response.headers.get('retry-after')
        print(f'Response 429. Sleeping for {retryAfter} seconds')
        time.sleep(int(retryAfter))

        # Keep current albums alredy fetched and keep fetching
        albumsList = albumsList + getAlbums(artistId=artistId, url=url)

    else:
        raise RuntimeError('Bad Request. Halting code')

    if albumsList:
        return albumsList
    else:
        return []