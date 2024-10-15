import requests
import json
import pprint
import time
import base64
import random

client_id = ''
client_secret = ''
access_token = ''
refresh_token = ''


def updateComposerAlbums():
    with open(r'C:\Users\leonardo.calasans\Desktop\MusicPearls\data\composers.json', encoding='utf-8') as fp:
        composers = json.load(fp)
    composers = composers['composers']
    for i in range(28, 29):
        print(f'Fetching albums of {composers[i]["name"]}')
        composerAlbums = getAlbums(composers[i]["id"])

        composerAlbumsJson = {'albums': composerAlbums}
        with open(f'albums2/albums_{composers[i]["id"]}.json', 'w', encoding='utf-8') as f:
            json.dump(composerAlbumsJson, f)

        time.sleep(10)

def getAlbums(artistId, url=''):
    global access_token
    if not url:
        url = 'https://api.spotify.com/v1/artists/' + artistId + '/albums?limit=50'

    albumsList = []
    print(url)
    response = requests.get(url, headers={'Authorization': f'Bearer {access_token}'})
    if response.status_code == 200:
        responseJson = response.json()
        items = responseJson['items']
        print(len(items))
        for i in range(len(items)):
            albumsList.append(items[i]['id'])
        if responseJson['next']:
            # print(len(albumsList))
            time.sleep(2)
            albumsList = albumsList + getAlbums(artistId=artistId, url=responseJson['next'])
        if albumsList:
            return albumsList
        else:
            return []

    # If unauthorized, re-authenticate and request again
    elif response.status_code == 401:
        print(f'Reponse 401. Getting new token')
        access_token = getNewToken()
        albumsList = albumsList + getAlbums(artistId=artistId, url=url)

    # If over-request, wait and retry afterwards
    elif response.status_code == 429:
        retryAfter = response.headers.get('retry-after')
        print(f'Response 429. Sleeping for {retryAfter} seconds')
        time.sleep(int(retryAfter))
        albumsList = albumsList + getAlbums(artistId=artistId, url=url)

    else:
        raise RuntimeError('Bad Request. Halting code')

def getNewToken():
    url = 'https://accounts.spotify.com/api/token'
    auth_client = client_id + ":" + client_secret
    auth_encode = 'Basic ' + base64.b64encode(auth_client.encode()).decode()
    response = requests.post(url,
                             headers={'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': auth_encode},
                             data={'grant_type': 'refresh_token', 'refresh_token': refresh_token})
    if response.status_code == 200:
        responseJson = response.json()
        return responseJson['access_token']
    else:
        raise RuntimeError('Unable to refresh Access Token')


# # getNewToken()
# # getAlbums(artistId='0enRaCZSvIUa2nVC7I4roi')
updateComposerTracks()



# # getNewToken()
# # getAlbums(artistId='0enRaCZSvIUa2nVC7I4roi')
# updateComposerAlbums()