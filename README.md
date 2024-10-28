# Pearls Parser - the official data source for [Music Pearls](https://github.com/MusicPearls)

Welcome to the Pearls Parser repo. This project is designed to fetch data from Spotify and parse the tracks to group all tracks related to the same work, normalizing their popularities. 
The data this generates is used by [Music Pearls](https://www.musicpearls.org/)


## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Data Structure](#data-structure)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Features

- **Spotify Scraper**: Fetches all albums, tracks and details of tracks for composers listed in the `composers.json` file.
- **Pearls Parser**: Groups tracks representing the same work using either predefined regex rules or AI with the OpenAI API.

## Prerequisites

- Generated Spotify API credentials (Client ID and Client Secret)
- Generated an OpenAI API key

## Installation

1. **Clone the repository**:
   ```sh
   git clone https://github.com/MusicPearls/Pearls-Parser.git
   cd Pearls-Parser
   ```

2. **Create a virtual environment**:
   ```sh
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the required packages**:
   ```sh
   pip install -r requirements.txt
   ```

## Configuration

1. **Set up environment variables**:
   Create a `.env` file in the root directory and add your Spotify API credentials and OpenAI GPT API key:
   ```env
   CLIENT_ID=your_spotify_client_id
   CLIENT_SECRET=your_spotify_client_secret
   OPENAI_API_KEY=your_openai_api_key
   ```

2. **Configure `composers.json`**:
   Ensure your `composers.json` file is correctly formatted and placed in the `data` folder:

## Usage

1. **Fetch Albums and Tracks**:
   Run the main and choose the desired option. Options 1-4 are related to scraping:
   ```sh
   python main.py
   ```

2. **Parse and Group Tracks**:
   Coming soon


## Data Structure

The `composers.json` file should be formatted as follows:
```json
{
  "composers": [
    {
      "name": "{name of the composer}",
      "id": "",
    },
  ]
}
```
The `id` field can be empty and will be populated by the `updateComposerInfo` function.

The album fetch will complete by generating files named `albums_{id}.json` in the data/albums folder. Each file will be formatted as follows:
```json
{
  "albums": [
      "{id of the album in Spotify}",
  ]
}
```

The track fetch will be based on the albums folder and will complete by generating files named `tracks_{id}.json` in the data/tracks folder. Each file will be formatted as follows:
```json
{
  "tracks": [
      "{id of the track in Spotify}",
  ]
}
```

The track details fetch will be based on the tracks folder and will complete by generating files named `tracksDetails_{id}.json` in the data/tracksDetails folder. Each file will be formatted as follows:
```json
{
    "tracks": [
        {
            "name": "{name of the track}"
            "id": "{id of the track}"
            "composer": "{name of composer}"
            "artists": [
                "{name of artists involved in track other than the composer}"
            ],
            "popularity": "{Spotify popularity of the track}"
        },
  ]
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments
- [Spotify Web API](https://developer.spotify.com/documentation/web-api/)
- [OpenAI API](https://beta.openai.com/docs/api-reference/introduction)
  
