import SpotifyScraper
import SpotifyScraper.getAlbums
import SpotifyScraper.getComposerInfo
import SpotifyScraper.getTrackDetails
import SpotifyScraper.getTracks
import SpotifyScraper.utils
import Parsers.AiParser
import Parsers.RegexParser
import os


def main():

    print(' 1: updateComposers \n 2: getAlbums \n 3: getTracks \n 4: getTracksDetails \n 5: Initial Regex Parse \n 6: Create OpenAI Batches \n 7: Start Uploading OpenAI Batches')
    option = int(input("Choose function: "))
    if option == 1:
        SpotifyScraper.getComposerInfo.updateComposerInfo()
    if option == 2:
        SpotifyScraper.getAlbums.updateComposerAlbums()
    if option == 3:
        SpotifyScraper.getTracks.updateComposerTracks()
    if option == 4:
        SpotifyScraper.getTrackDetails.updateComposerTrackDetails()
    if option == 5:
        opus_handler = Parsers.RegexParser.RegexParser()
        opus_handler.getTracks()
        opus_handler.parseOpus()
    if option == 6:
        Parsers.AiParser.batchCreator()
    if option == 7:
        Parsers.AiParser.manageBatches()

main()
