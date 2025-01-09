# Classical Music Metadata Parser
This repository is responsible for generating the data consumed by the [Music Pearls](https://github.com/MusicPearls/MusicPearls) web application, which provides an intuitive interface for exploring classical music works and their popularity.

## Overview

This project fetches and analyzes classical music data from Spotify to standardize metadata and calculate work popularity:
1. Scrapes track information from Spotify for composers listed in composers.json
2. Standardizes track names through regex pattern matching and AI analysis
3. Groups tracks that belong to the same musical work (e.g. movements of a Symphony)
4. Calculates popularity metrics for complete musical works based on their constituent tracks

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
   git clone https://github.com/yourusername/classical-music-metadata-parser.git
   cd classical-music-metadata-parser
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
   
   # Create composers.json with your desired composers
   # Example structure (Spotify IDs can be left blank. They will be populated by getComposerInfo.py):
   # {
   #   "composers": [
   #     {
   #       "name": "Ludwig van Beethoven",
   #       "spotifyId": "",
   #     }
   #   ]
   # }
   touch data/composers.json
   ```
