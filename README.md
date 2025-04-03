# Classical Music Metadata Parser
This repository is responsible for generating the data consumed by the [Music Pearls](https://github.com/MusicPearls/MusicPearls) web application, which provides an intuitive interface for exploring classical music works and their popularity.

## Overview

This project can:
1. Fetch track information from Spotify for composers listed in composers.json
2. Standardize track names through regex pattern matching and AI analysis
3. Group tracks that belong to the same musical work (e.g. movements of a Symphony)
4. Calculate popularity metrics for complete musical works based on their constituent tracks
5. Fetch and apply custom categorization rules 

## Features

- Spotify integration for fetching composer albums, tracks and track details
- Regex-based parsing for initial standardization of track names
- AI-powered analysis using OpenAI's GPT models to standardize track names
- Support for common classical music catalogs (BWV, K., Op., etc.)
- Recognition of standard musical forms (Symphony, Concerto, Sonata, etc.)
- Grouping tracks into complete musical works and calculating popularity metrics of the full work, not just individual movements or tracks

## Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/MusicPearls/Pearls-Parser.git
   cd Pearls-Parser
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   
   # On Windows
   .\venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   # Copy the template file
   cp .env.template .env
   
   # Edit .env file with your credentials:
   # - SPOTIFY_CLIENT_ID=your_spotify_client_id
   # - SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
   # - OPENAI_API_KEY=your_openai_api_key
   ```


5. Create required directories and files:
   ```bash
   # Create data directory
   mkdir data
   
   # Create composers.json with desired composers
   # {
   #   "composers": [
   #     {
   #       "name": "Ludwig van Beethoven",
   #        "id": "",
            "birthyear": ""
   #     }
   #   ]
   # }
   ```

6. Run entrypoint to select functions:
   ```bash
   python main.py
   ```

## Updating Data (SpotifyScraper)
1. updateComposers: fetches id for composers in data/composers.json
2. getAlbums: fetches all albums from composers in data/composers.json. Saves albums id's in data/albums/albums_{composerId}.json
3. getTracks: fetches id's of all tracks from all albums from previous step. Saves in data/tracks/tracks_{composerId}.json
4. getTracksDetails: fetches details of all tracks from previous step. saves list of objects in data/tracksDetails/tracksDetails_{composerId}.json
   ```bash
    trackDetails object:
       {
         "name": str",
         "id": str,
         "composer": str,
          "artists": list(str),
         "popularity": int
      }
   ```

## Parsing Data (Parsers/RegexParser)
1. Run RegexParser functions:
    1. parseOpus: 
        1.  gets all tracks from data/tracksDetails
        2.  categorizes track by applying regex rules in name
        3.  generates track catalog
        4.  creates opusName
        5.  saves in data/regexParsed.json
    2. applyCustomRules:
        1. fetches custom rules from data/customRules.csv (csv must have columns: composer, name, form, opusName)
        2. reads all previous parsed tracks from data/regexParsed.json
        3. applies custom rules: if track name contains {name}, its form = {form} and opusName = {opusName}
        4. overwrites data/regexParsed.json
    3. postProcess:
        1. filters out uncategorized tracks
        2. groups tracks by opusName
        3. counts number or recordings for each opus
        4. adds representativity metric for each opus
        5. normalizes popularity by composer and by form
        6. saves in data/processedTracks.json

## Parsing Data with AI (Parsers/AiParser)
It's possible to use OpenAI to generate the opusName of the tracks. It's handled using batch requests:
1. batchCreator: reads data/regexParsed.json and generates the batch files in data/gptBatches
2. manageBatches: uploads as many batches as possible within the token limit, waits until completion, saves reponse in data/aiTracks/aiTracks_{batchNumber}.json, and so on
3. mergeAiTracks: reads all tracks in data/aiTracks folder and groups into data/AiParsed.json in the same format as data/regexParsed.json
