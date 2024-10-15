import requests
import json
import pprint
import time
import base64
import random



client_id = ''
client_secret = ''
global access_token
access_token = ''
refresh_token = ''


def updateComposerTracks():
    with open(r'C:\Users\leonardo.calasans\Desktop\MusicPearls\data\composers.json', encoding='utf-8') as fp:
        composers = json.load(fp)
    composers = composers['composers']

    for i in range(6, 25):
        print('------------------------------------------')
        print(f'Fetching tracks of {composers[i]["name"]}')
        print('------------------------------------------')
        composerTracks = getComposerTracks(composers[i]["id"])
        composerTracksJson = {'tracks': composerTracks}
        with open(f'tracks2/tracks_{composers[i]["id"]}.json', 'w', encoding='utf-8') as f:
            json.dump(composerTracksJson, f)
        time.sleep(10*(random.random()+1))


def getComposerTracks(artistId):
    with open(fr'C:\Users\leonardo.calasans\Desktop\MusicPearls\data\albums2\albums_{artistId}.json',
              encoding='utf-8') as fp:
        albums = json.load(fp)
    albums = albums['albums']
    composerTracks = []
    for j in range(len(albums)):
        print(f'Album: {albums[j]}')
        albumTracks = getAlbumTracks(albums[j], artistId)
        composerTracks = composerTracks + albumTracks
        time.sleep(5*(random.random()+1))
    return composerTracks


def getAlbumTracks(albumId, artistId, url=''):
    global access_token
    if not url:
        url = 'https://api.spotify.com/v1/albums/' + albumId + '/tracks?limit=50'
    albumTracks = []
    response = requests.get(url, headers={'Authorization': f'Bearer {access_token}'})

    if response.status_code == 200:
        responseJson = response.json()
        items = responseJson['items']
        for i in range(len(items)):
            if artistInTrack(items[i], artistId):
                albumTracks.append(items[i]['id'])
        if responseJson['next']:
            time.sleep(1 * (random.random()))
            albumTracks = albumTracks + getAlbumTracks(albumId=albumId, artistId=artistId, url=responseJson['next'])
        return albumTracks

    # If unauthorized, re-authenticate and request again
    elif response.status_code == 401:
        print(f'Reponse 401. Getting new token')
        access_token = getNewToken()
        albumTracks = albumTracks + getAlbumTracks(albumId=albumId, artistId=artistId, url=url)
        return albumTracks

    # If over-request, wait and retry afterwards
    elif response.status_code == 429:
        retryAfter = response.headers.get('retry-after')
        print(f'Response 429. Sleeping for {retryAfter} seconds')
        time.sleep(int(retryAfter))
        albumTracks = albumTracks + getAlbumTracks(albumId=albumId, artistId=artistId, url=url)
        return albumTracks

    else:
        print(response)
        print(response.json())
        raise RuntimeError('Bad Request. Halting code')


def artistInTrack(track, artistId):
    trackArtists = track['artists']
    for k in range(len(trackArtists)):
        if trackArtists[k]['id'] == artistId:
            return True
    return False


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


# getNewToken()
# getAlbums(artistId='0enRaCZSvIUa2nVC7I4roi')
updateComposerTracks()
