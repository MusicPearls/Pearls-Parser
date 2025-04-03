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

    print(' 1: updateComposers \n 2: getAlbums \n 3: getTracks \n 4: getTracksDetails \n 5: Run all Regex Parser functions '
    '\n 6: Regex Parser parseOpus \n 7: Regex Parser applyCustomRules \n 8: Regex Parser postProcess \n 9: Saves CSV files from regexParsed')
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
        opus_handler.parseOpus()
        opus_handler.applyCustomRules()
        opus_handler.postProcess()
    if option == 6:
        opus_handler = Parsers.RegexParser.RegexParser()
        opus_handler.parseOpus()
    if option == 7:
        opus_handler = Parsers.RegexParser.RegexParser()
        opus_handler.applyCustomRules()
    if option == 8:
        opus_handler = Parsers.RegexParser.RegexParser()
        opus_handler.postProcess()
    if option == 9:
        opus_handler = Parsers.RegexParser.RegexParser()
        opus_handler.regexParsedToCSV()


        
main()
