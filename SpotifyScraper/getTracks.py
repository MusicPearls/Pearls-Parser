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
client_id = os.environ.get("CLIENT_ID_1")
client_secret = os.environ.get("CLIENT_SECRET_1")

def updateComposerTracks():
    """
    Fetches all the tracks of the albums in data/albums
    """

    global access_token
    access_token = None
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Get all composers
    with open(os.path.join(script_dir, '../data/composers.json'), encoding='utf-8') as fp:
        composers = json.load(fp)
    composers = composers['composers']

    # Get all existing tracks files
    files = os.listdir(os.path.join(script_dir, '../data/tracks'))
    pattern = re.compile(r'tracks_(.+)\.json')
    existingIds = [pattern.match(file).group(1) for file in files if pattern.match(file)]

    i = 0
    while i < len(composers):
    # i = len(composers) - 1
    # while i > 0:
        composerName = composers[i]['name']
        composerId = composers[i]['id']
        if composerId in existingIds:
            print(f'Skipping tracks fetch of {composerName}')
            i = i + 1
            # i = i - 1
        else:
            print('------------------------------------------')
            print(f'Fetching tracks of {composerName}')
            print('------------------------------------------')
            composerTracks = getComposerTracks(composerId)
            uniqueTracks = list(set(composerTracks))
            composerTracksJson = {'tracks': uniqueTracks}
            with open(os.path.join(script_dir, f'../data/tracks/tracks_{composerId}.json'), 'w', encoding='utf-8') as f:
                json.dump(composerTracksJson, f, ensure_ascii=False)
            time.sleep(10*(random.random()+1))
            i = i + 1
            # i = i - 1

def getComposerTracks(artistId):
    """
    Fetches all tracks from a given composer

    Returns:
        list[str]: list with all tracks ids
    """

    script_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(script_dir, f"../data/albums/albums_{artistId}.json"), encoding='utf-8') as fp:
        albums = json.load(fp)
    albums = albums['albums']
    composerTracks = []
    for i in range(len(albums)):
        print(f'Album: {albums[i]}')
        albumTracks = getAlbumTracks(albums[i], artistId)
        composerTracks = composerTracks + albumTracks
        time.sleep(1*(random.random()+1))
    return composerTracks

def getAlbumTracks(albumId, artistId, url=''):
    """
    Fetches all tracks from a given album

    Returns:
        list[str]: list with all tracks ids from the album
    """

    global access_token
    if not url:
        url = 'https://api.spotify.com/v1/albums/' + albumId + '/tracks?limit=50'
    albumTracks = []
    print(url)
    response = requests.get(url, headers={'Authorization': f'Bearer {access_token}'})

    if response.status_code == 200:
        responseJson = response.json()
        items = responseJson['items']
        for i in range(len(items)):
            if artistInTrack(items[i], artistId):
                albumTracks.append(items[i]['id'])
        if responseJson['next']:
            time.sleep(1 * (1 + random.random()))
            albumTracks = albumTracks + getAlbumTracks(albumId=albumId, artistId=artistId, url=responseJson['next'])

    # If unauthorized, re-authenticate and request again
    elif response.status_code == 401:
        print(f'Reponse 401. Getting new token')
        access_token = utils.getNewToken(client_id, client_secret)
        albumTracks = albumTracks + getAlbumTracks(albumId=albumId, artistId=artistId, url=url)

    # If over-request, wait and retry afterwards
    elif response.status_code == 429:
        retryAfter = response.headers.get('retry-after')
        print(f'Response 429. Sleeping for {retryAfter} seconds')
        time.sleep(int(retryAfter))
        albumTracks = albumTracks + getAlbumTracks(albumId=albumId, artistId=artistId, url=url)

    else:
        print(response.json())
        print('Bad Request, trying again')
        time.sleep(int(600))
        albumTracks = albumTracks + getAlbumTracks(albumId=albumId, artistId=artistId, url=url)

    
    if albumTracks:
        return albumTracks
    else:
        return []

def artistInTrack(track, artistId):
    """
    Checks if given artist is part of the artists of the track
    """

    trackArtists = track['artists']
    for k in range(len(trackArtists)):
        if trackArtists[k]['id'] == artistId:
            return True
    return False
