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
import time
import chardet

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
MAX_TOKENS_PER_REQUEST = 5000
MAX_REQUESTS_PER_BATCH = 100
MAX_BATCH_QUEUE = 1000000
USER_PROMPT = f"""
I will give you a list of JSON objects, each containing the information of a classical music track from Spotify. Your task is to populate the fields 'form' and 'opusName' for each track based on the 'name' field of the track. Here are the detailed instructions:\n

1. **Form Field:**
- The 'form' field should represent the musical form that best matches this track or the overall piece it is part of.
- Use one of the following musical forms: {musicalForms}.
- If the musical form is unclear or not in the given list, return 'unknown' as the value of the 'form' field.

2. **OpusName Field:**
- The 'opusName' field should be the name that best represents the track or the overall work it is part of, excluding information about movement and tonality.
- Preferably, use the format: [musical form] No. [number] [catalog]. [catalog number].
- These are example of catalogs, but feel free to use others not provided here: {catalogs}.
- If the number is unclear, omit the No. [number] from the opusName,
- If there is no catalog, omit the [catalog] and [catalog number] fields from the opusName,
- If there is no catalog number, omit both the [catalog] and [catalog number] fields from the opusName.
- If returning the opusName in the given format, do not add any other information that is not in the format.
- If the piece is best known by another name that is not in the given format, use that name instead.
- Use the shortest possible name that accurately represents the piece.
- Remove any special characters that do not constitute the name of the piece.
- If the piece is part of a larger work, use the name of the larger work as the opusName.

3. **Examples:**
- Input: "name": "Symphony No. 5 in C Minor, Op. 67: I. Allegro con brio"
    - Output: "form": "Symphony", "opusName": "Symphony No. 5 Op. 67"
- Input: "name": "Piano Concerto No. 21 in C Major, K. 467: II. Andante"
    - Output: "form": "Piano Concerto", "opusName": "Piano Concerto No. 21 K. 467"
- Input: "name": "Mahler: Symphony No. 4 in G Major: I. Heiter, bedächtig. Nicht eilen"
    - Output: "form": Symphony", "opusName": "Symphony No. 4"
- Input: "name: "Bagatelle No. 25 in A minor, WoO 59"
    - Output: "form": "Bagatelle", "opusName": "Für Elise"

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
- Make sure to return a valid JSON object with the specified fields for each track.
"""

SYSTEM_PROMPT = """
You are an expert in classical music with extensive knowledge of musical forms, compositions, and catalogs. 
Your task is to analyze and categorize classical music tracks based on their names, providing accurate and detailed information about their musical form and opus name."""
SCRIPT_START_TIME = datetime.now()

def batchCreator():
    """
    Creates the batches for OpenAI batches API for all tracks in RegexParsed.json
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(script_dir, './RegexParsed.json'), encoding='utf-8') as fp:
        tracks = json.load(fp)

    total_cost = 0
    # Split the trackDetails file
    splitTrackDetails = tokenChunkSplitter(tracks, max_tokens=MAX_TOKENS_PER_REQUEST - INITIAL_PROMPTS_TOKENS)

    # Create the requests for the batches
    requests = []
    for chunk in splitTrackDetails:
        batchPrompt = USER_PROMPT + f"\n\n This is the objects list: {json.dumps(chunk, ensure_ascii=False)}"
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
                {"custom_id": f"batch-{nBatches}-req-{j}", 
                 "method": "POST", 
                 "url": "/v1/chat/completions", 
                 "body": batchRequests[j]})
        with open(os.path.join(script_dir, f'../data/gptBatches/New/batch_{nBatches}.jsonl'), 'w', encoding='utf-8') as f:
            for obj in batch:
                json_line = json.dumps(obj, ensure_ascii=False)
                f.write(json_line + '\n')
        nBatches = nBatches + 1
        i = i + MAX_REQUESTS_PER_BATCH
    
    enc = tiktoken.get_encoding("o200k_base")
    tokens = enc.encode(json.dumps(tracks, ensure_ascii=False))
    total_cost_mini = len(tokens) * 0.075/1000000
    print(f"Total cost for gpt-4o-mini: ${total_cost_mini}")

    print("Ensuring UTF-8 encoding...")
    ensureUTF8()

def manageBatches():
    max_retries = 1
    retry_delay = 60
    
    while True:
        try:
            # Check if there are any files left in the New folder
            script_dir = os.path.dirname(os.path.abspath(__file__))
            new_batches_path = os.path.join(script_dir, '../data/gptBatches/New')
            if not os.listdir(new_batches_path):
                print("No more batches to process. Exiting.")
                break

            # Step 1: Check the status of the batches
            getBatchesStatus()
            
            # Step 2: Handle completed batches
            handleFinishedBatches()
            
            # Step 3: Upload all possible batches within the queue token limit
            QueueBatches()
            
            # Step 4: Wait for 30 minutes
            print("Waiting for 30 minutes...")
            time.sleep(1800)
            

            
        except Exception as e:
            print(f"Error in batch management: {str(e)}")
            for i in range(max_retries):
                print(f"Retrying in {retry_delay} seconds... (Attempt {i+1}/{max_retries})")
                time.sleep(retry_delay)
                try:
                    # Try to resume from where we left off
                    getBatchesStatus()
                    handleFinishedBatches()
                    break
                except Exception as retry_e:
                    print(f"Retry {i+1} failed: {str(retry_e)}")
                    if i == max_retries - 1:
                        raise RuntimeError("Max retries exceeded")

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

def get_batch_files(directory):
    """Helper function to get only valid batch files"""
    batch_pattern = re.compile(r'^batch_\d+\.jsonl$')
    return [f for f in os.listdir(directory) if batch_pattern.match(f)]

def QueueBatches():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    new_batches_path = os.path.join(script_dir, '../data/gptBatches/New')
    batch_files = get_batch_files(new_batches_path)
    
    # Sort batch files numerically based on their batch number
    batch_files.sort(key=lambda x: int(re.search(r'batch_(\d+)\.jsonl', x).group(1)))
    
    in_progress_tokens = getInProgressTokens()
    for filename in batch_files:
        batch_tokens = getBatchTokens(f'../data/gptBatches/New/{filename}')
        if in_progress_tokens + batch_tokens <= MAX_BATCH_QUEUE:
            uploadBatch(filename)
            in_progress_tokens += batch_tokens
            print(f"Batch {filename} uploaded")

def getBatchesStatus():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    batches = client.batches.list()
    batchesJson = []
    
    # Get the start of the current day
    today_start = SCRIPT_START_TIME.replace(day=21, hour=0, minute=0, second=0, microsecond=0)
    
    for batch in batches:
        created_at = datetime.fromtimestamp(batch.created_at)
        if created_at > today_start:
            completed_at = datetime.fromtimestamp(batch.completed_at).strftime('%Y-%m-%d %H:%M') if batch.completed_at else None
            batchesJson.append({
                'id': batch.id,
                'status': batch.status,
                'created_at': created_at.strftime('%Y-%m-%d %H:%M'),
                'completed_at': completed_at,
                "output_file_id": batch.output_file_id,
                "error_file_id": batch.error_file_id,
                "metadata": batch.metadata
            })
    with open(os.path.join(script_dir, f'../data/gptBatches/batchStatus.json'), 'w', encoding='utf-8') as file:
        json.dump(batchesJson, file, ensure_ascii=False)
        print("batchStatus file updated")

def handleFinishedBatches():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(script_dir, f'../data/gptBatches/batchStatus.json'), 'r', encoding='utf-8') as file:
        batches = json.load(file)

    for batch in batches:
        if batch['status'] in ["completed", "failed"] and batch['metadata']:
            filename = batch['metadata']['filename']
            inProgressFiles = os.listdir(os.path.join(script_dir, f'../data/gptBatches/InProgress'))

            if filename in inProgressFiles:
                # Handle failed batches
                if batch['status'] == "failed":
                    shutil.move(os.path.join(script_dir, f'../data/gptBatches/InProgress/{filename}'), 
                              os.path.join(script_dir, f'../data/gptBatches/Error/{filename}'))
                    
                    if batch['error_file_id']:
                        errorFileId = batch['error_file_id']
                        error_response = client.files.content(errorFileId).text
                        errorJson = []
                        for line in error_response.splitlines():
                            errorJson.append(json.loads(line))

                        with open(os.path.join(script_dir, f'../data/gptBatches/Error/error_{filename}.json'), 'w', encoding='utf-8') as f:
                            json.dump(errorJson, f, ensure_ascii=False)
                    print(f'Failed batch {filename} moved to Error')
                    continue

                # Handle completed batches with errors
                if batch['error_file_id']:
                    shutil.move(os.path.join(script_dir, f'../data/gptBatches/InProgress/{filename}'), 
                        os.path.join(script_dir, f'../data/gptBatches/Error/{filename}'))
        
                    errorFileId = batch['error_file_id']
                    error_response = client.files.content(errorFileId).text
                    errorJson = []
                    for line in error_response.splitlines():
                        errorJson.append(json.loads(line))

                    with open(os.path.join(script_dir, f'../data/gptBatches/Error/error_{filename}.json'), 'w', encoding='utf-8') as f:
                        json.dump(errorJson, f, ensure_ascii=False)
                    print(f'Batch {filename} moved to Error')

                # Move to Finished and get batch responses
                else:          
                    # Get batch responses
                    responseJson = []
                    batchFileId = batch['output_file_id']
                    file_response = client.files.content(batchFileId).text
                    for line in file_response.splitlines():
                        batchResponse = FixJsonLine(line)
                        response = FixJsonLine(batchResponse['response']['body']['choices'][0]['message']['content'])
                        responseJson.append(response)

                    pattern = r'batch_(\d+)\.jsonl'
                    match = re.search(pattern, filename)
                    batchNo = match.group(1)
                    with open(os.path.join(script_dir, f'../data/aiTracks/aiTracks_{batchNo}.json'), 'w', encoding='utf-8') as f:
                        json.dump(responseJson, f, ensure_ascii=False)
                    shutil.move(os.path.join(script_dir, f'../data/gptBatches/InProgress/{filename}'), 
                        os.path.join(script_dir, f'../data/gptBatches/Finished/{filename}')) 

def tokenChunkSplitter(tracks, max_tokens):
    enc = tiktoken.get_encoding("o200k_base")
    tokens = enc.encode(json.dumps(tracks, ensure_ascii=False))
    chunks = []
    current_chunk = []
    current_chunk_tokens = 0

    for track in tracks:
        track_tokens = enc.encode(json.dumps(track, ensure_ascii=False))
        if current_chunk_tokens + len(track_tokens) > max_tokens:
            chunks.append(current_chunk)
            current_chunk = []
            current_chunk_tokens = 0
        current_chunk.append(track)
        current_chunk_tokens += len(track_tokens)

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

def FixJsonLine(line):
    # Attempt to fix common JSON issues
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        # Try to fix common issues
        fixed_line = line
        if line.count('"') % 2 != 0:
            fixed_line += '"'
        if fixed_line[-1] != '}':
            fixed_line += '}'
        try:
            return json.loads(fixed_line)
        except json.JSONDecodeError:
            return None

def getBatchTokens(filepath):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(script_dir, filepath), 'r', encoding='utf-8') as f:
        batch_content = f.read()
    enc = tiktoken.get_encoding("o200k_base")
    return len(enc.encode(batch_content))

def getInProgressTokens():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    in_progress_path = os.path.join(script_dir, '../data/gptBatches/InProgress')
    batch_files = get_batch_files(in_progress_path)
    in_progress_tokens = 0
    for filename in batch_files:
        batch_tokens = getBatchTokens(f'../data/gptBatches/InProgress/{filename}')
        in_progress_tokens += batch_tokens
    return in_progress_tokens

def ensureUTF8():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    new_batches_path = os.path.join(script_dir, '../data/gptBatches/New')
    batch_files = get_batch_files(new_batches_path)
    
    for filename in batch_files:
        full_path = os.path.join(new_batches_path, filename)
        
        # First, make a backup of the file
        backup_path = full_path + '.backup'
        shutil.copy2(full_path, backup_path)
        
        try:
            # Detect the file encoding
            with open(full_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding']
            
            # Read the file with the detected encoding
            with open(full_path, 'r', encoding=encoding) as f:
                lines = f.readlines()
            
            # Write each line back as UTF-8, ensuring valid JSON lines
            with open(full_path, 'w', encoding='utf-8') as f:
                for line in lines:
                    try:
                        json_line = json.loads(line)
                        f.write(json.dumps(json_line, ensure_ascii=False) + '\n')
                    except json.JSONDecodeError as e:
                        print(f"Invalid JSON line in {filename}: {line}")
                        print(f"Error: {str(e)}")
                        # Restore from backup
                        shutil.copy2(backup_path, full_path)
                        raise RuntimeError(f"Invalid JSON line in {filename}")
            
            # Remove backup if successful
            os.remove(backup_path)
            
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            # Restore from backup
            shutil.copy2(backup_path, full_path)
            raise

def mergeAiTracks():
    """
    Merges all aiTracks_*.json files into a single file with the same format as RegexParsed.json
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ai_tracks_dir = os.path.join(script_dir, '../data/aiTracks')
    
    # Check if the directory exists
    if not os.path.exists(ai_tracks_dir):
        print(f"Error: The directory '{ai_tracks_dir}' does not exist.")
        return
    
    # Get all aiTracks files
    ai_files = [f for f in os.listdir(ai_tracks_dir) if f.startswith('aiTracks_') and f.endswith('.json')]
    
    # Sort files numerically
    ai_files.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))
    
    # Merge all tracks
    all_tracks = []
    for file in ai_files:
        with open(os.path.join(ai_tracks_dir, file), 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                try:
                    all_tracks.extend(item['tracks'])
                except Exception as e:
                    print(f"Error parsing {file}: {item}")
                    print(str(e))
                    continue

    output_path = os.path.join(script_dir, './AiParsed.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_tracks, f, ensure_ascii=False, indent=2)
    
    print(f"Successfully merged {len(ai_files)} files containing {len(all_tracks)} tracks")