import requests
import base64

def getNewToken(client_id, client_secret):
    """
    Fetches new access token from Spotify

    Returns:
        string: the new access token
    """
    
    token_url = "https://accounts.spotify.com/api/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }

    response = requests.post(token_url, headers=headers, data=data)

    if response.status_code == 200:
        token_info = response.json()
        access_token = token_info.get("access_token")
        return access_token
    else:
        print("Failed to retrieve access token:", response.status_code, response.text)