import pandas as pd
import json
import os
from os import listdir
from os.path import isfile, join
from decimal import Decimal
import re
import numpy as np

pd.options.mode.chained_assignment = None


musicalForms = [
    "Symphony", "Symphonie", 'Sinfonie', 'Symfonie', 'Symfonia',
    "Piano Concerto", 'Keyboard Concerto', 'Klavierkonzert', 'Concerto pour piano',
    'Violin Concerto', 'Cello Concerto', 'Flute Concerto', 'Clarinet Concerto', 'Trumpet Concerto',
    'Oboe Concerto', 'Bassoon Concerto', 'Horn Concerto', 'Viola Concerto', 'Clarinet Concerto',
    "Piano Sonata", "Klaviersonate", "Sonata per pianoforte",
    'Violin Sonata', 'Cello Sonata', 'Clarinet Sonata', 'Oboe Sonata', 'Horn Sonata', 'Viola Sonata', 'Bassoon Sonata', 'Horn Sonata', 'Flute Sonata', 'Trumpet Sonata'
    "String Quartet", "String Trio",
    'Piano Trio', 'Keyboard Trio',
    'Piano Quartet', 'Keyboard Quartet',
    'Quintet', 'Sextet', 'Octet',
    "Mass", 'Missa',
    'Song',
    'Requiem',
    "Oratorio",
    "Cantata",
    "Ballet",
    "Suite",
    "Overture",
    'Bagatelle', 'Bagatelles',
    "Prelude", "Preludes", 'Prélude', 'Préludes',
    "Fugue",
    "Rhapsody",
    "Etude", 'Etudes', 'Étude', 'Études',
    "Nocturne", 'Nocturnes',
    "Waltz",
    "Mazurka",
    "Polonaise",
    "Rondo",
    "Impromptu",
    "Scherzo",
    'Variations', 'Variation',
    "Minuet",
    "Gavotte",
    "Toccata",
    "Fantasia",
    'Ecossaises', 'Ecossaise', 'Écossaise', 'Écossaises',
    'Dance', 'Dances', 'Danses', 'Danse',
]

formsMapping = {
    "Symphony": ["Symphony", "Symphonie", "Sinfonie", "Symfonie", "Symfonia"],
    "Piano Concerto": ["Piano Concerto", "Keyboard Concerto", "Klavierkonzert", "Concerto pour piano"],
    "Piano Sonata": ["Piano Sonata", "Klaviersonate", "Sonata per pianoforte"],
    "Bagatelle": ["Bagatelle", "Bagatelles"],
    "Prelude": ["Prelude", "Preludes", 'Prélude', 'Préludes'],
    "Etude": ["Etude", 'Etudes', 'Étude', 'Études'],
    "Nocturne": ["Nocturne", 'Nocturnes'],
    'Variations': ['Variations', 'Variation'],
    'Ecossaises': ['Ecossaises', 'Ecossaise', 'Écossaise', 'Écossaises'],
    'Dance': ['Dance', 'Dances', 'Danses', 'Danse'],
    'Piano Trio': ['Keyboard Trio', 'Piano Trio'],
    'Piano Quartet': ['Keyboard Quartet', 'Piano Quartet'],
    "Mass": ['Missa', "Mass"],
}

catalogs = ['Op. ', 'Op.', 'Op ', 'BWV. ', 'BWV.', 'K. ', 'K.', 'D. ', 'D.',
            'H. ', 'H.', 'Hob. ', 'Hob.', 'S. ', 'S.', 'L.', 'L. ', 'M.', 'M. ',
            'BWV.', 'BWV. ', 'BWV', 'BWV ', 'WoO. ', 'WoO.', 'WoO ', 'WoO', 'RV ',
            'RV. ', 'RV', 'RV.', 'R.', 'R', 'R. ', 'R ']


class RegexParser():
    def __init__(self):
        self.tracks = None
        self.formOpus = None
        self.composerOpus = None
        self.fullOpus = None
        self.uncategorizedTracks = None

    def parseOpus(self):
        """
        Method responsible for handling the categorization of tracks
        """

        def categorize(name):
            """
            Function that searches for musical form keyword in the name of the track

            Parameters
            ----------
            name: name of the track
            """
            name_lower = name.lower()
            for keyword in musicalForms:
                if keyword.lower() in name_lower:
                    return keyword
            return ''

        def getNo(name):
            """
            Function that searches for the number of the track in its name

            Parameters
            ----------
            name: name of the track
            """

            match = re.search(r'No. (\d+)', name)
            match2 = re.search(r'No.(\d+)', name)
            match3 = re.search(r'No . (\d+)', name)
            match4 = re.search(r'No .(\d+)', name)
            match5 = re.search(r'No (\d+)', name)
            if match:
                return match.group(1)
            elif match2:
                return match2.group(1)
            elif match3:
                return match3.group(1)
            elif match4:
                return match4.group(1)
            elif match5:
                return match5.group(1)
            else:
                return ''

        def getOp(name):
            """
            Function that searches for the opus number and catalog in the track name

            Parameters
            ----------
            name: name of the track
            """

            for keyword in catalogs:
                name_lower = name.lower()
                keyword_lower = re.escape(keyword.lower())
                match = re.search(rf'{keyword_lower}(\d+)', name_lower)
                if match:
                    clean_keyword = keyword.replace(' ', '').replace('.', '')
                    return match.group(1), clean_keyword
            return '', ''

        def createOpusName(row, columns):
            """
            Function that creates the full opus name from available information

            Parameters
            ----------
            row: row of the tracks dataframe
            columns: columns from the tracks dataframe used to create the full opus name
            """

            # Create opus name with form, number and catalog number
            opusname = row.loc[columns[1]]
            if row.loc[columns[2]]:
                opusname = opusname + ' No. ' + str(row.loc[columns[2]])
            if row.loc[columns[3]]:
                opusname = opusname + ' ' + str(row.loc[columns[4]]) + '. ' + str(row.loc[columns[3]])

            # If there is no catalog number nor number in the name, return the full name of the piece
            if opusname == row.loc[columns[1]]:
                opusname = row.loc[columns[0]]

            return opusname

        def findOpus(df):
            """
            Function that gets works with number and without catalog number and try to get the
            catalog number from other entries of this work in the dataframe

            Parameters
            ----------
            df: the original tracks dataframe
            """

            no_op_df = df[(df['op'] == '') & (df['number'] != '')]
            op_df = df[(df['op'] != '') & (df['number'] != '')]
            grouped_no_op = no_op_df[['composer', 'number', 'form']].groupby(
                by=['composer', 'number', 'form']).sum().reset_index()
            found_op_df = pd.DataFrame(columns=['composer', 'number', 'form', 'found_op'])
            for index, row in grouped_no_op.iterrows():
                match_df = op_df[(op_df['composer'] == row['composer']) &
                                 (op_df['number'] == row['number']) &
                                 (op_df['form'] == row['form'])]
                if not match_df.empty:
                    found_op = match_df['op'].mode().iloc[0]
                    found_catalog = match_df['catalog'].mode().iloc[0]
                    count_op = (match_df['op'] == found_op).sum()
                    count_no_op = no_op_df[(no_op_df['composer'] == row['composer']) &
                                           (no_op_df['number'] == row['number']) &
                                           (no_op_df['form'] == row['form'])]
                    count_no_op = (count_no_op['op'] == '').sum()

                    if count_op > count_no_op:
                        row['found_op'] = found_op
                        row['found_catalog'] = found_catalog
                        found_op_df = pd.concat([found_op_df, pd.DataFrame([row])], ignore_index=True)

            df = df.merge(found_op_df, how='left', on=['composer', 'number', 'form']).fillna('')
            df['op'] = np.where(df['op'] == '', df['found_op'], df['op'])
            df['catalog'] = np.where(df['catalog'] == '', df['found_catalog'], df['catalog'])
            return df

        def formMapper(work_name, mapper):
            """
            Function that normalizes the names of musical forms to the standard
            given in the mapper constant

            Parameters
            ----------
            work_name: the name of the musical form
            mapper: the mapper dictionary
            """

            for key, value in mapper.items():
                for variant in value:
                    if variant.lower() in work_name.lower():
                        return key
            return work_name

        def convert_to_int(value):
            """
            Function that converts some value to integer but keeps empty values as empty
            """

            if value == '':
                return ''
            return int(value)

        # Fetch tracks
        script_dir = os.path.dirname(os.path.abspath(__file__))
        print('Fetching Tracks...\n')
        self.getTracks()

        # Categorizing tracks
        print('Categorizing Tracks...\n')
        df = self.tracks.copy()
        df['form'] = df['name'].apply(categorize)
        categorized_df = df[df['form'] != '']
        uncategorized_df = df[df['form'] == '']

        # Joining equivalent categories
        categorized_df['stantardized_form'] = categorized_df['form'].apply(lambda x: formMapper(x, formsMapping))
        categorized_df['form'] = categorized_df['stantardized_form']
        print(f'Categorized {len(categorized_df.index)} of {len(df.index)} tracks ({int((len(categorized_df.index)/(len(df.index)))*100)}%) ')

        # Getting catalog of tracks
        print('Getting catalog of tracks...\n')
        categorized_df['number'] = categorized_df['name'].apply(getNo)
        categorized_df[['op', 'catalog']] = categorized_df['name'].apply(getOp).apply(pd.Series)
        categorized_df['popularity'] = categorized_df['popularity'].apply(convert_to_int)
        categorized_df['op'] = categorized_df['op'].apply(convert_to_int)
        categorized_df['number'] = categorized_df['number'].apply(convert_to_int)
        print('Finding catalog of tracks based on other tracks...')
        categorized_df['form'] = categorized_df['stantardized_form']
        categorized_df = findOpus(categorized_df)

        # Creating opus name
        print('Creating opus name of tracks...\n')
        categorized_df['opusname'] = categorized_df.apply(lambda row: createOpusName(row, ['name', 'form', 'number', 'op', 'catalog']), axis=1)

        print('Finishing up...\n')
        categorized_df = categorized_df[['name', 'composer', 'opusname', 'form', 'id', 'popularity', 'artists']]
        uncategorized_df['opusname'] = ''
        uncategorized_df['form'] = ''
        parsed_df = pd.concat([categorized_df, uncategorized_df[['name', 'composer', 'opusname', 'form', 'id', 'popularity', 'artists']]], ignore_index=True)
        parsed_df.to_json(os.path.join(script_dir, '../data/parsedTracks/RegexParsed.json'), 
                          orient='records', 
                          force_ascii=False)

    def applyCustomRules(self):
        """
        Fetches the custom rules from customRules.csv and applies
        them into the initial RegexParsed.json
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        print('Applying custom rules...\n')

        # Load custom rules and tracks into DataFrames
        rules_df = pd.read_csv(os.path.join(script_dir, 'customRules.csv'))
        tracks_df = pd.read_json(os.path.join(script_dir, '../data/parsedTracks/RegexParsed.json'))
        
        # Convert names to lowercase for matching
        rules_df['name_lower'] = rules_df['name'].str.lower()
        tracks_df['name_lower'] = tracks_df['name'].str.lower()
        
        # For each rule, find and update matching tracks
        for _, rule in rules_df.iterrows():
            mask = (tracks_df['name_lower'].str.contains(rule['name_lower'], na=False)) & \
                   (tracks_df['composer'] == rule['composer'])
            
            if mask.any():
                tracks_df.loc[mask, 'form'] = rule['form']
                tracks_df.loc[mask, 'opusname'] = rule['opusName']
        
        # Drop the temporary lowercase column and save
        tracks_df = tracks_df.drop('name_lower', axis=1)
        tracks_df.to_json(
            os.path.join(script_dir, '../data/parsedTracks/RegexParsed.json'),
            orient='records',
            force_ascii=False,
            indent=2
        )

    def postProcess(self):
        """
        Post-processes the RegexParsed tracks by:
        1. Filtering out uncategorized tracks
        2. Grouping by opus
        3. Adding recording counts
        4. Filtering by recording count threshold
        5. Normalizing popularity in both form and composer contexts
        6. Finding representative tracks
        """
        def readAndFilterTracks():
            """Reads the RegexParsed.json file and filters out uncategorized tracks"""
            script_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(script_dir, '../data/parsedTracks/RegexParsed.json')
            
            # Read and filter tracks
            df = pd.read_json(file_path)
            return df[(df['opusname'].str.len() > 0) & (df['form'].str.len() > 0)].copy()

        def groupByOpus(df):
            """Groups tracks by opus and calculates mean popularity"""
            return df.groupby(['opusname', 'composer', 'form']).agg({
                'popularity': 'mean'
            }).reset_index()

        def addRecordingCount(df, original_df):
            """Adds recording count based on opusname + composer combinations"""
            recording_counts = original_df.groupby(['opusname', 'composer']).size().reset_index(name='recordingCount')
            return df.merge(recording_counts, on=['opusname', 'composer'])

        def filterByRecordingCount(df, min_recordings=50, min_tracks_per_group=10):
            """
            Filters tracks based on recording count, ensuring minimum representation
            for each composer and form. Also adds relevance flags indicating why each
            track was included in the final dataset.
            """
            # First get tracks meeting the recording threshold
            high_recording_df = df[df['recordingCount'] >= min_recordings].copy()
            high_recording_df['composerRelevant'] = True
            high_recording_df['formRelevant'] = True
            
            # Get all unique composers and forms
            all_composers = df['composer'].unique()
            all_forms = df['form'].unique()
            
            # Check composer groups
            composer_counts = high_recording_df['composer'].value_counts()
            composers_needing_tracks = [
                composer for composer in all_composers 
                if composer_counts.get(composer, 0) < min_tracks_per_group
            ]
            
            # Check form groups
            form_counts = high_recording_df['form'].value_counts()
            forms_needing_tracks = [
                form for form in all_forms 
                if form_counts.get(form, 0) < min_tracks_per_group
            ]
            
            # For each composer needing tracks, add their top tracks
            additional_composer_tracks = []
            for composer in composers_needing_tracks:
                composer_tracks = df[df['composer'] == composer]
                needed = min_tracks_per_group - composer_counts.get(composer, 0)
                if needed > 0:
                    top_tracks = composer_tracks[~composer_tracks.index.isin(high_recording_df.index)] \
                        .nlargest(needed, 'recordingCount')
                    top_tracks['composerRelevant'] = True
                    top_tracks['formRelevant'] = False
                    additional_composer_tracks.append(top_tracks)
            
            # For each form needing tracks, add top tracks
            additional_form_tracks = []
            for form in forms_needing_tracks:
                form_tracks = df[df['form'] == form]
                needed = min_tracks_per_group - form_counts.get(form, 0)
                if needed > 0:
                    top_tracks = form_tracks[~form_tracks.index.isin(high_recording_df.index)] \
                        .nlargest(needed, 'recordingCount')
                    top_tracks['composerRelevant'] = False
                    top_tracks['formRelevant'] = True
                    additional_form_tracks.append(top_tracks)
            
            # Combine all dataframes
            final_df = pd.concat(
                [high_recording_df] + 
                additional_composer_tracks + 
                additional_form_tracks
            ).drop_duplicates()
            
            return final_df.sort_values('recordingCount', ascending=False)

        def normalizePopularity(df):
            """
            Performs log-normalization of popularity in two contexts:
            1. Within each musical form (formPopularity) - using only form-relevant tracks
            2. Within each composer's works (composerPopularity) - using only composer-relevant tracks
            Both normalizations account for recording counts and range from 0 to 100
            """
            # Calculate base popularity with increased weight on log-normalized recording count
            df['p_log_r'] = df['popularity'] * (np.log1p(df['recordingCount']) ** 2)
            
            # Normalize by form (using only form-relevant tracks)
            form_relevant = df[df['formRelevant']].copy()
            form_max = form_relevant.groupby('form')['p_log_r'].transform('max')
            form_relevant['formPopularity'] = 100 * (form_relevant['p_log_r'] / form_max)
            
            # Normalize by composer (using only composer-relevant tracks)
            composer_relevant = df[df['composerRelevant']].copy()
            composer_max = composer_relevant.groupby('composer')['p_log_r'].transform('max')
            composer_relevant['composerPopularity'] = 100 * (composer_relevant['p_log_r'] / composer_max)
            
            # Merge the normalized popularities back to the main dataframe
            df = df.merge(
                form_relevant[['opusname', 'composer', 'formPopularity']], 
                on=['opusname', 'composer'], 
                how='left'
            )
            df = df.merge(
                composer_relevant[['opusname', 'composer', 'composerPopularity']], 
                on=['opusname', 'composer'], 
                how='left'
            )
            
            # Clean up intermediate columns
            df = df.drop(columns=['p_log_r'])
            
            return df

        def addRepresentativeTrack(df, original_df):
            """Adds the ID of the most popular track for each opus"""
            # For each opus, find the track with highest popularity
            representative_tracks = original_df.sort_values('popularity', ascending=False) \
                .groupby(['opusname', 'composer']) \
                .agg({'id': 'first'}) \
                .reset_index() \
                .rename(columns={'id': 'representativeTrack'})
            
            return df.merge(representative_tracks, on=['opusname', 'composer'])

        # Main processing pipeline
        print("Starting post-processing...")
        
        # 1. Read and filter tracks
        print("Reading and filtering tracks...")
        original_df = readAndFilterTracks()
        
        # 2. Group by opus
        print("Grouping tracks by opus...")
        processed_df = groupByOpus(original_df)
        
        # 3. Add recording count
        print("Adding recording counts...")
        processed_df = addRecordingCount(processed_df, original_df)
        
        # 4. Filter by recording count
        print("Filtering tracks by recording count...")
        processed_df = filterByRecordingCount(processed_df)
        
        # 5. Normalize popularity
        print("Normalizing popularity...")
        processed_df = normalizePopularity(processed_df)
        
        # 6. Add representative track
        print("Adding representative tracks...")
        processed_df = addRepresentativeTrack(processed_df, original_df)
        
        # Clean up and organize columns
        final_columns = [
            'opusname', 'composer', 'form', 'formPopularity', 
            'composerPopularity', 'recordingCount', 'representativeTrack',
            'composerRelevant', 'formRelevant'
        ]
        processed_df = processed_df[final_columns]
        
        # Save the result
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(script_dir, '../data/parsedTracks/ProcessedTracks.json')
        processed_df.to_json(output_path, orient='records', force_ascii=False, indent=2)
        
        print("Post-processing completed!")
        return processed_df

    def getTracks(self):
        """
        Method that gets all tracks from tracksDetails files
        """

        # Read all files from tracksDetails
        script_dir = os.path.dirname(os.path.abspath(__file__))
        folderPath = os.path.abspath(os.path.join(script_dir, '../data/tracksDetails'))
        trackFiles = [f for f in listdir(folderPath) if isfile(join(folderPath, f))]

        # Getting all tracks
        if not self.tracks:
            self.tracks = pd.DataFrame(data=None, columns=['name', 'id', 'composer', 'artists', 'popularity'])
        for i in range(len(trackFiles)):
            # Open file in path and create dataframe from the json
            file_path = os.path.join(folderPath, trackFiles[i])
            with open(file_path, encoding='utf-8') as fp:
                d = json.load(fp)
            d = d['tracks']
            df = pd.DataFrame.from_records(d)

            # Remove lines where composer is not the one being considered
            track_composers = df['composer'].value_counts()
            main_composer = track_composers.idxmax()
            df = df[df['composer'] == main_composer]
            self.tracks = pd.concat([self.tracks, df], ignore_index=True)

    def regexParsedToCSV(self):
        """
        Saves RegexParsed.json in CSV
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(script_dir, '../data/parsedTracks/RegexParsed.json')
        
        # Read JSON into dataframe
        df = pd.read_json(json_path)
        
        # Sort by composer and popularity
        df = df.sort_values(['composer', 'popularity'], ascending=[True, False])
        
        # Calculate chunk size
        chunk_size = len(df) // 4
        
        # Split and save chunks
        for i in range(4):
            start_idx = i * chunk_size
            end_idx = start_idx + chunk_size if i < 3 else len(df)
            chunk = df.iloc[start_idx:end_idx]
            
            csv_path = os.path.join(script_dir, f'../data/parsedTracks/RegexParsed_chunk{i+1}.csv')
            chunk.to_csv(csv_path, encoding='utf-8', index=False)

opus_handler = RegexParser()
# opus_handler.parseOpus()
# opus_handler.applyCustomRules()
opus_handler.postProcess()