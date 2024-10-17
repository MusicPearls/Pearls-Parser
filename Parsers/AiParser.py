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
import shutil
from datetime import datetime

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

"""
# of tokens:
    - userPrompt: 1050
    - systemPrompt: 50

Token limits (gpt-4o-mini):
    - Batch queue: 2.000.000
    - Request: 200.000
    - Context Window: 128.000
    - Max Output: 16.384
"""

INITIAL_PROMPTS_TOKENS = 2000
MAX_TOKENS_PER_REQUEST = 20000
MAX_REQUESTS_PER_BATCH = 100
USER_PROMPT = f"""
I will give you a list of JSON objects, each containing the information of a classical music track from Spotify. Your task is to create the fields 'form' and 'opusName' for each track based on the 'name' field of the track. Here are the detailed instructions:\n

1. **Form Field:**
- The 'form' field should represent the musical form that best matches this track or the piece it is part of.
- Use one of the following musical forms: {musicalForms}.
- If the musical form is unclear or not in the given list, return 'unknown' as the value of the 'form' field.

2. **OpusName Field:**
- The 'opusName' field should be the name that best represents the track or the piece it is part of, excluding information about movement and tonality.
- Preferably, use the format: [musical form] No. [number] [catalog]. [catalog number].
- These are example of catalogs, but feel free to use others not mapped here: {catalogs}.
- If the number is unclear, omit the No. [number] from the opusName,
- If there is no catalog, omit the catalog and catalog number from the opusName,
- If there is no catalog number, omit both the catalog and catalog number from the opusName.
- If returning the opusName in the given format, do not add any other information that is not in the format.
- If the piece is best known by another name that is not in the given format, use that name instead.

3. **Examples:**
- Input: "name": "Symphony No. 5 in C Minor, Op. 67: I. Allegro con brio"
    - Output: "form": "Symphony", "opusName": "Symphony No. 5 Op. 67"
- Input: "name": "Piano Concerto No. 21 in C Major, K. 467: II. Andante"
    - Output: "form": "Piano Concerto", "opusName": "Piano Concerto No. 21 K. 467"
- Input: "name": "Mahler: Symphony No. 4 in G Major: I. Heiter, bedächtig. Nicht eilen"
    - Output: "form": Symphony", "opusName": "Symphony No. 4"

4. **Handling Ambiguity:**
- If multiple forms or catalogs could apply, choose the most commonly recognized one.
- If there is still ambiguity, return 'unknown' for the 'form' field and leave out the catalog and number from the 'opusName'.

5. **Output**
- The output should be a JSON with the format {{'tracks': [object]}} where object should be: 
{{
    'id': the original id field,
    'form': the form field specified before
    'opusName': the opusName field specified before}}
- Be consistent in the categorization of the tracks. Different movements or parts of the same piece should end up with the same opusName.
"""

SYSTEM_PROMPT = """
You are an expert in classical music with extensive knowledge of musical forms, compositions, and catalogs. 
Your task is to analyze and categorize classical music tracks based on their names, providing accurate and detailed information about their musical form and opus name."""



def batchCreator():
    """
    Creates the batches for OpenAI batches API for all composers
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(script_dir, '../data/composers.json'), encoding='utf-8') as fp:
        composers = json.load(fp)
    composers = composers['composers']
    total_cost = 0
    for composer in composers:
        if not os.path.exists(os.path.join(script_dir, f"../data/tracksDetails/tracksDetails_{composer['id']}.json")):
            print(f'TracksDetails of {composer['name']} not found. Skipping')
        else:
            print(f'Generating batch requests for {composer['name']}')
            total_cost = total_cost + composerBatchCreator(composer['id'])
    print(f"Total cost for gpt-4o-mini: ${total_cost}")


def composerBatchCreator(composerId):
    """
    Creates batches for a given composer

    Returns:
        int: total cost to process the generated batches
    """

    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Split the trackDetails file
    with open(os.path.join(script_dir, f'../data/tracksDetails/tracksDetails_{composerId}.json'), encoding='utf-8') as fp:
        tracksDetailsText = fp.read()
    splitTrackDetails = tokenChunkSplitter(tracksDetailsText, max_tokens=MAX_TOKENS_PER_REQUEST - INITIAL_PROMPTS_TOKENS)

    # Create the requests for the batches
    requests = []
    for chunk in splitTrackDetails:
        batchPrompt = USER_PROMPT + f"\n\n This is the objects list: {chunk}"
        requests.append({
        "model": "gpt-4o-mini",
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": batchPrompt
            }
        ]
        })

    # Generate the batches
    nBatches = 0
    i = 0
    while i < len(requests):
        batchRequests = requests[i:i+MAX_REQUESTS_PER_BATCH]
        batch = []
        for j in range(len(batchRequests)):
            batch.append(
                {"custom_id": f"{composerId}-batch-{nBatches}-req-{j}", 
                 "method": "POST", 
                 "url": "/v1/chat/completions", 
                 "body": batchRequests[j]})
        with open(os.path.join(script_dir, f'../data/gptBatches/New/batch_{composerId}_{nBatches}.jsonl'), 'w', encoding='utf-8') as f:
            for obj in batch:
                json_line = json.dumps(obj)
                f.write(json_line + '\n')
        nBatches = nBatches + 1
        i = i + MAX_REQUESTS_PER_BATCH
    
    enc = tiktoken.get_encoding("o200k_base")
    tokens = enc.encode(tracksDetailsText)
    return len(tokens) * 0.075/1000000


def queueBatches():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    inProgressFiles = os.listdir(os.path.join(script_dir, f'../data/gptBatches/New'))
    print(inProgressFiles)    

def batchTokens(filepath):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    with open(filepath, 'r', encoding='utf-8') as file:
        batchRequests = json.load(file)
        print(batchRequests)


def uploadBatch(filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    batch_input_file = client.files.create(
        file=open(os.path.join(script_dir, f'../data/gptBatches/New/{filename}'), "rb"), 
        purpose="batch"
        )
    batchObject = client.batches.create(
                    input_file_id=batch_input_file.id,
                    endpoint="/v1/chat/completions",
                    completion_window="24h",
                    metadata={"filename": filename}
                    )
    
    shutil.move(os.path.join(script_dir, f'../data/gptBatches/New/{filename}'), 
                os.path.join(script_dir, f'../data/gptBatches/InProgress/{filename}'))
    return batchObject


def getBatches():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    batches = client.batches.list()
    batchesJson = []
    for batch in batches:
        created_at = datetime.fromtimestamp(batch.created_at).strftime('%Y-%m-%d %H:%M') if batch.created_at else None
        completed_at = datetime.fromtimestamp(batch.completed_at).strftime('%Y-%m-%d %H:%M') if batch.completed_at else None
        batchesJson.append({
            'id': batch.id,
            'status': batch.status,
            'created_at': created_at,
            'completed_at': completed_at,
            "output_file_id": batch.output_file_id,
            "error_file_id": batch.error_file_id,
            "metadata": batch.metadata
        })
    with open(os.path.join(script_dir, f'../data/gptBatches/batchStatus.json'), 'w', encoding='utf-8') as file:
        json.dump(batchesJson, file, ensure_ascii=False)

def handleFinishedBatches():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(script_dir, f'../data/gptBatches/batchStatus.json'), 'r', encoding='utf-8') as file:
        batches = json.load(file)

    for batch in batches:
        if batch['status'] == "completed":

            # Move batch file to Finished
            filename = batch['metadata']['filename']
            inProgressFiles = os.listdir(os.path.join(script_dir, f'../data/gptBatches/InProgress'))
            if filename in inProgressFiles:
                shutil.move(os.path.join(script_dir, f'../data/gptBatches/InProgress/{filename}'), 
                    os.path.join(script_dir, f'../data/gptBatches/Finished/{filename}')) 
        
                # Get batch responses
                responseJson = []
                batchFileId = batch['output_file_id']
                file_response = client.files.content(batchFileId).text
                for line in file_response.splitlines():
                    batchResponse = json.loads(line)
                    responseJson.append(json.loads(batchResponse['response']['body']['choices'][0]['message']['content']))

                pattern = r'batch_(.*?)_(\d+)\.jsonl'
                match = re.search(pattern, filename)
                composerId = match.group(1)
                batchNumber = match.group(2)
                with open(os.path.join(script_dir, f'../data/categorizedTracks/categorizedTracks_{composerId}_{batchNumber}_.json'), 'w', encoding='utf-8') as f:
                    json.dump(responseJson, f, ensure_ascii=False)
            else:
                print(f'Batch {filename} not In Progress')


def aiTest():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(script_dir, '../data/tracksDetails/tracksDetails_2ANtgfhQkKpsW6EYSDqldz.json'), encoding='utf-8') as fp:
        tracksDetailsText = fp.read()
    splitTrackDetails = tokenChunkSplitter(tracksDetailsText, max_tokens=MAX_TOKENS_PER_REQUEST)

    completion = client.chat.completions.create(
    model="gpt-4o-mini",
    response_format= { "type": "json_object" },
    temperature=0.2,
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
    chunks = [tokens[i:i + max_tokens] for i in range(0, len(tokens), max_tokens)]
    text_chunks = [enc.decode(chunk) for chunk in chunks]
    return text_chunks
