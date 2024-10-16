import pandas as pd
import json
from decimal import Decimal
import re
import numpy as np
from openai import OpenAI
import os
from dotenv import load_dotenv
import re
import tiktoken

load_dotenv()
openai_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=openai_key)

musicalForms = [
    "Symphony",
    "Piano Concerto",
    'Violin Concerto', 'Cello Concerto', 'Flute Concerto', 'Clarinet Concerto', 'Trumpet Concerto',
    'Oboe Concerto', 'Bassoon Concerto', 'Horn Concerto', 'Viola Concerto',
    "Piano Sonata",
    'Violin Sonata', 'Cello Sonata', 'Clarinet Sonata', 'Oboe Sonata', 'Horn Sonata', 'Viola Sonata', 'Bassoon Sonata',
    "String Quartet", "String Trio",
    'Piano Trio',
    'Piano Quartet',
    'Quintet', 'Sextet', 'Octet',
    "Mass",
    'Requiem',
    "Oratorio",
    "Cantata",
    "Opera",
    "Ballet",
    "Suite",
    "Overture",
    'Bagatelle',
    "Prelude",
    "Fugue",
    "Rhapsody",
    "Etude",
    "Nocturne",
    "Waltz",
    "Mazurka",
    "Polonaise",
    'Variations',
    'Ecossaises',
    'Dance',
    'Song',
]

catalogs = ['Op. ', 'Op.', 'Op ', 'BWV. ', 'BWV.', 'K. ', 'K.', 'D. ', 'D.',
            'H. ', 'H.', 'Hob. ', 'Hob.', 'S. ', 'S.', 'L.', 'L. ', 'M.', 'M. ',
            'BWV.', 'BWV. ', 'BWV', 'BWV ', 'WoO. ', 'WoO.', 'WoO ', 'WoO']

def AiParser():

    enc = tiktoken.get_encoding("o200k_base")
    script_dir = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(script_dir, '../data/tracksDetails/tracksDetails_2ANtgfhQkKpsW6EYSDqldz.json'), encoding='utf-8') as fp:
        tracksDetailsText = fp.read()
    
    splitTrackDetails = tokenChunkSplitter(tracksDetailsText, max_tokens=3000)

    
    userPrompt = f"""
    I will give you a list of JSON objects, each containing the information of a classical music track from Spotify. Your task is to create the fields 'form' and 'opusName' for each track based on the 'name' field of the track. Here are the detailed instructions:\n

    1. **Form Field:**
    - The 'form' field should represent the musical form that best matches this track or the piece it is part of.
    - Use one of the following musical forms: {musicalForms}.
    - If the musical form is unclear or not in the given list, return 'unknown' as the value of the 'form' field.

    2. **OpusName Field:**
    - The 'opusName' field should be the name that best represents the track or the piece it is part of, excluding information about movement and tonality.
    - Preferably, use the format: [musical form] No. [number] [catalog]. [catalog number].
    - These are example of catalogs, but feel free to use others not mapped here: {catalogs}.
    - If the number is unclear, omit the No. [number] from the opusName.
    - If the catalog or catalog number is unclear, omit the [catalog]. and [catalog number] from the opusName.
    - If returning the opusName in the given format, do not add any other information that is not in the format.
    - If the piece is best known by another name that is not in the given format, use that name instead.

    3. **Examples:**
    - Input: "name": "Symphony No. 5 in C Minor, Op. 67: I. Allegro con brio"
        - Output: "form": "Symphony", "opusName": "Symphony No. 5 Op. 67"
    - Input: "name": "Piano Concerto No. 21 in C Major, K. 467: II. Andante"
        - Output: "form": "Piano Concerto", "opusName": "Piano Concerto No. 21 K. 467"
    
    4. **Handling Ambiguity:**
    - If multiple forms or catalogs could apply, choose the most commonly recognized one.
    - If there is still ambiguity, return 'unknown' for the 'form' field and leave out the catalog and number from the 'opusName'.

    5. **Output**
    - Be sure to return the same JSON list of the input, only with the added fields in each entry.
    - Be consistent in the categorization of the tracks. Different movements or parts of the same piece should end up with the same opusName.
    
    This is the list of objects: {splitTrackDetails[4]}
    """

    systemPrompt = """
    You are an expert in classical music with extensive knowledge of musical forms, compositions, and catalogs. 
    Your task is to analyze and categorize classical music tracks based on their names, providing accurate and detailed information about their musical form and opus name."""


    # Create the batch payload
    batch_payload = []
    for i, chunk in enumerate(splitTrackDetails):
        userPrompt = f"""
        I will give you a list of JSON objects, each containing the information of a classical music track from Spotify. Your task is to create the fields 'form' and 'opusName' for each track based on the 'name' field of the track. Here are the detailed instructions:\n

        1. **Form Field:**
        - The 'form' field should represent the musical form that best matches this track or the piece it is part of.
        - Use one of the following musical forms: {musicalForms}.
        - If the musical form is unclear or not in the given list, return 'unknown' as the value of the 'form' field.

        2. **OpusName Field:**
        - The 'opusName' field should be the name that best represents the track or the piece it is part of, excluding information about movement and tonality.
        - Preferably, use the format: [musical form] No. [number] [catalog]. [catalog number].
        - These are example of catalogs, but feel free to use others not mapped here: {catalogs}.
        - If either the number or catalog are unclear, omit them from the opusName.
        - If returning the opusName in the given format, do not add any other information that is not in the format.
        - If the piece is best known by another name that is not in the given format, use that name instead.

        3. **Examples:**
        - Input: "name": "Symphony No. 5 in C Minor, Op. 67: I. Allegro con brio"
            - Output: "form": "Symphony", "opusName": "Symphony No. 5 Op. 67"
        - Input: "name": "Piano Concerto No. 21 in C Major, K. 467: II. Andante"
            - Output: "form": "Piano Concerto", "opusName": "Piano Concerto No. 21 K. 467"
        
        4. **Handling Ambiguity:**
        - If multiple forms or catalogs could apply, choose the most commonly recognized one.
        - If there is still ambiguity, return 'unknown' for the 'form' field and leave out the catalog and number from the 'opusName'.

        5. **Output**
        - Be sure to return the same JSON list of the input, only with the added fields in each entry.
        - Be consistent in the categorization of the tracks. Different movements or parts of the same piece should end up with the same opusName.
        
        This is the list of objects: {chunk}
        """
        
        batch_payload.append({
            "model": "gpt-4o-mini",
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": systemPrompt
                },
                {
                    "role": "user",
                    "content": userPrompt
                }
            ]
        })

    # Write the batch payload to a JSON file
    batch_file_path = os.path.join(script_dir, '../data/batchPayload/batch_payload.json')
    os.makedirs(os.path.dirname(batch_file_path), exist_ok=True)
    with open(batch_file_path, 'w', encoding='utf-8') as fp:
        json.dump(batch_payload, fp, ensure_ascii=False, indent=4)

    print(f"Batch payload has been written to {batch_file_path}")


    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format= { "type": "json_object" },
        messages=[
            {
                "role": "system", 
                "content": systemPrompt 
            },
            {
                "role": "user", 
                "content": userPrompt}
        ]
    )

    response = json.loads(completion.choices[0].message.content)
    # Write the data to a JSON file
    with open(os.path.join(script_dir, f'../data/categorizedTracks/categorizedTracks_1.json'), 'w', encoding='utf-8') as fp:
        json.dump(response, fp, ensure_ascii=False)


def tokenChunkSplitter(text, max_tokens):
    enc = tiktoken.get_encoding("o200k_base")
    tokens = enc.encode(text)
    print(f"Total input tokens: {len(tokens)}")
    print(f"Total gpt-4o-mini cost: {len(tokens)* 0.15/1000000}")
    chunks = [tokens[i:i + max_tokens] for i in range(0, len(tokens), max_tokens)]
    text_chunks = [enc.decode(chunk) for chunk in chunks]
    return text_chunks