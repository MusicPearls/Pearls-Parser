import pandas as pd
import json
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
    'Oboe Concerto', 'Bassoon Concerto', 'Horn Concerto', 'Viola Concerto',
    "Piano Sonata", "Klaviersonate", "Sonata per pianoforte",
    'Violin Sonata', 'Cello Sonata', 'Clarinet Sonata', 'Oboe Sonata', 'Horn Sonata', 'Viola Sonata', 'Bassoon Sonata',
    "String Quartet", "String Trio",
    'Piano Trio', 'Keyboard Trio',
    'Piano Quartet', 'Keyboard Quartet',
    'Quintet', 'Sextet', 'Octet',
    "Mass", 'Missa',
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
            'BWV.', 'BWV. ', 'BWV', 'BWV ', 'WoO. ', 'WoO.', 'WoO ', 'WoO']


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
                        found_op_df = found_op_df.append(row, ignore_index=True)

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

        def normalizePopularity(df, type):
            """
            Function that makes the log-normalization of the popularity of the track
            in the context of either all tracks of the same musical form or all tracks
            of the same composer

            Parameters
            ----------
            df: the original tracks dataframe
            type: normalize in the context of musical form or of composer
            """

            if type == 'Form':
                unique_forms = df['form'].unique()
                form_max = pd.DataFrame(columns=['form', 'max_p_log_r'])
                for f in unique_forms:
                    form_df = df[df['form'] == f]
                    form_df['p_log_r'] = form_df['popularity'] * np.log1p(form_df['nrecordings'])
                    max_plogr = form_df['p_log_r'].max()
                    form_max = form_max.append({'form': f, 'max_p_log_r': max_plogr}, ignore_index=True)

                df['p_log_r'] = df['popularity'] * np.log1p(df['nrecordings'])
                df = df.merge(form_max, how='left', on='form')
                df['formPopularity'] = 100 * (df['p_log_r'] / df['max_p_log_r'])
                df = df.drop(columns=['p_log_r', 'max_p_log_r'])
                return df
            elif type == 'Composer':
                unique_composers = df['composer'].unique()
                composer_max = pd.DataFrame(columns=['composer', 'max_p_log_r'])
                for f in unique_composers:
                    composer_df = df[df['composer'] == f]
                    composer_df['p_log_r'] = composer_df['popularity'] * np.log1p(composer_df['nrecordings'])
                    max_plogr = composer_df['p_log_r'].max()
                    composer_max = composer_max.append({'composer': f, 'max_p_log_r': max_plogr}, ignore_index=True)

                df['p_log_r'] = df['popularity'] * np.log1p(df['nrecordings'])
                df = df.merge(composer_max, how='left', on='composer')
                df['composerPopularity'] = 100 * (df['p_log_r'] / df['max_p_log_r'])
                df = df.drop(columns=['p_log_r', 'max_p_log_r'])
                return df

        def convert_to_int(value):
            """
            Function that converts some value to integer but keeps empty values as empty
            """

            if value == '':
                return ''
            return int(value)

        def removeLowRecordings(df, threshold, type):
            """
            Function that removes tracks with unrepresentative number of recordings
            while assuring that every musical form keeps at least 10 entries of works

            Parameters
            ----------
            df: the original tracks dataframe
            threshold: the number of recordings to qualify the opus as representative
            """

            if type == 'Form':
                unique_forms = df['form'].unique()
                keep_df = pd.DataFrame(columns=['op_artist'])
                opus_df = df[['op_artist', 'form', 'nrecordings']].groupby(by=['op_artist']) \
                    .agg({'form': 'first', 'nrecordings': 'first'}).reset_index()
                for f in unique_forms:
                    form_df = opus_df[opus_df['form'] == f]
                    high_rec_df = form_df[form_df['nrecordings'] >= threshold]
                    low_rec_df = form_df[form_df['nrecordings'] < threshold]
                    if len(high_rec_df) < 10:
                        low_rec_df = low_rec_df.sort_values(by='nrecordings', ascending=False)
                        low_rec_df = low_rec_df.head(10 - len(high_rec_df))
                        high_rec_df = high_rec_df.append(low_rec_df)
                    keep_df = keep_df.append(high_rec_df, ignore_index=True)

                keep_df = keep_df.drop(columns=['form', 'nrecordings'])
                keep_df['kept'] = True
                return keep_df

            elif type == 'Composer':
                unique_composer = df['composer'].unique()
                keep_df = pd.DataFrame(columns=['op_artist'])
                opus_df = df[['op_artist', 'composer', 'nrecordings']].groupby(by=['op_artist']) \
                    .agg({'composer': 'first', 'nrecordings': 'first'}).reset_index()
                for f in unique_composer:
                    comp_df = opus_df[opus_df['composer'] == f]
                    high_rec_df = comp_df[comp_df['nrecordings'] >= threshold]
                    low_rec_df = comp_df[comp_df['nrecordings'] < threshold]
                    if len(high_rec_df) < 10:
                        low_rec_df = low_rec_df.sort_values(by='nrecordings', ascending=False)
                        low_rec_df = low_rec_df.head(10 - len(high_rec_df))
                        high_rec_df = high_rec_df.append(low_rec_df)
                    keep_df = keep_df.append(high_rec_df, ignore_index=True)

                keep_df = keep_df.drop(columns=['composer', 'nrecordings'])
                keep_df['kept'] = True
                return keep_df

        # Categorizing tracks
        print('Categorizing Tracks...')
        df = self.tracks.copy()
        df['form'] = df['name'].apply(categorize)
        categorized_df = df[df['form'] != '']
        uncategorized_df = df[df['form'] == '']
        # categorized_df.to_csv('raw.csv', encoding='utf-8')

        # Joining equivalent categories
        categorized_df['stantardized_form'] = categorized_df['form'].apply(lambda x: formMapper(x, formsMapping))
        categorized_df['form'] = categorized_df['stantardized_form']
        print(f'Categorized {len(categorized_df.index)} of {len(df.index)} tracks ({int((len(categorized_df.index)/(len(df.index)))*100)}%) ')

        # Getting catalog of tracks
        print('Getting catalog of tracks...')
        categorized_df['number'] = categorized_df['name'].apply(getNo)
        categorized_df[['op', 'catalog']] = categorized_df['name'].apply(getOp).apply(pd.Series)
        categorized_df['popularity'] = categorized_df['popularity'].apply(convert_to_int)
        categorized_df['op'] = categorized_df['op'].apply(convert_to_int)
        categorized_df['number'] = categorized_df['number'].apply(convert_to_int)
        print('Joining same tracks with and without catalog...')
        categorized_df['form'] = categorized_df['stantardized_form']
        categorized_df = findOpus(categorized_df)

        # Creating opus name
        print('Creating opus name of tracks...')
        categorized_df['opusname'] = categorized_df.apply(lambda row: createOpusName(row, ['name', 'form', 'number', 'op', 'catalog']), axis=1)
        categorized_df['opusname_lower'] = categorized_df['opusname'].str.lower()

        # Getting number of recordings
        print('Getting number of recordings...')
        categorized_df['op_artist'] = categorized_df['opusname_lower'] + categorized_df['composer']
        recording_counts = categorized_df['op_artist'].value_counts().reset_index()
        recording_counts.columns = ['op_artist', 'nrecordings']
        recording_counts = recording_counts.sort_values(by=['nrecordings'], ascending=False)
        categorized_df = categorized_df.merge(recording_counts, on=['op_artist'], how='left')

        categorized_df.to_csv('output.csv', encoding='utf-8')
        # categorized_df = pd.read_csv('output.csv', encoding='utf-8', keep_default_na=False, na_filter=False)

        form_df = categorized_df.copy()
        composer_df = categorized_df.copy()

        # Remove opus with low number of recordings
        print('Removing unrepresentative tracks...')
        op_to_keep = removeLowRecordings(form_df, threshold=50, type='Form')
        form_df = form_df.merge(op_to_keep, how='left', on='op_artist')
        form_df = form_df[form_df['kept'] == True]
        form_df = form_df.drop(columns=['kept'])
        op_to_keep = removeLowRecordings(form_df, threshold=50, type='Composer')
        composer_df = composer_df.merge(op_to_keep, how='left', on='op_artist')
        composer_df = composer_df[composer_df['kept'] == True]
        composer_df = composer_df.drop(columns=['kept'])

        # Group the works
        form_df = form_df.groupby(by=['op_artist', 'composer']) \
            .agg({'opusname': 'first', 'popularity': 'mean', 'form': 'first', 'nrecordings': 'first'}).reset_index()
        composer_df = composer_df.groupby(by=['op_artist', 'composer']) \
            .agg({'opusname': 'first', 'popularity': 'mean', 'form': 'first', 'nrecordings': 'first'}).reset_index()

        # Normalize the popularity by the number of recordings
        print('Normalizing popularity...')
        form_df = normalizePopularity(form_df, 'Form')
        composer_df = normalizePopularity(composer_df, 'Composer')

        # Arrange columns
        form_df = form_df.rename(
            columns={'opusname': 'opusName', 'nrecordings': 'recordingCount'})
        composer_df = composer_df.rename(
            columns={'opusname': 'opusName', 'nrecordings': 'recordingCount'})
        categorized_df = categorized_df.rename(
            columns={'opusname': 'opusName', 'nrecordings': 'recordingCount'})
        form_df = form_df[['opusName', 'composer', 'form', 'formPopularity', 'recordingCount']]
        composer_df = composer_df[['opusName', 'composer', 'form', 'composerPopularity', 'recordingCount']]

        self.formOpus = form_df
        self.composerOpus = composer_df
        self.fullOpus = categorized_df
        self.uncategorizedTracks = uncategorized_df

    def getTracks(self):
        """
        Method that gets all tracks from tracksDetails files
        """

        # Read all files from trackDetails
        folderPath = r'C:\Users\leonardo.calasans\Desktop\MusicPearls\data\tracksDetails2'
        trackFiles = [f for f in listdir(folderPath) if isfile(join(folderPath, f))]

        # Getting all tracks
        if not self.tracks:
            self.tracks = pd.DataFrame(data=None, columns=['name', 'id', 'composer', 'artists', 'popularity'])
        for i in range(len(trackFiles)):
            # Open file in path and create dataframe from the json
            with open(folderPath + r'\\' + trackFiles[i], encoding='utf-8') as fp:
                d = json.load(fp)
            d = d['tracks']
            df = pd.DataFrame.from_records(d)

            # Remove lines where composer is not the one being considered
            track_composers = df['composer'].value_counts()
            main_composer = track_composers.idxmax()
            df = df[df['composer'] == main_composer]
            self.tracks = self.tracks.append(df)

    def saveLocal(self):
        self.formOpus.to_json('form_opus.json', orient='records', force_ascii=False)
        self.composerOpus.to_json('composer_opus.json', orient='records', force_ascii=False)
        self.uncategorizedTracks.to_json('uncategorized.json', orient='records', force_ascii=False)


opus_handler = OpusParser()
opus_handler.getTracks()
opus_handler.parseOpus()
opus_handler.saveLocal()
