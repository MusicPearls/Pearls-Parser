import SpotifyScraper
import SpotifyScraper.getAlbums
import SpotifyScraper.getComposerInfo
import SpotifyScraper.getTrackDetails
import SpotifyScraper.getTracks
import SpotifyScraper.utils
import Parsers.AiParser

def main():

    print(' 1: updateComposers \n 2: getAlbums \n 3: getTracks \n 4: getTracksDetails \n 5: Create OpenAI Batches \n 6: Upload OpenAI Batches \n 7: Check batches \n 8: Handle finished batches')
    option = int(input("Choose function: "))
    if option == 1:
        SpotifyScraper.getComposerInfo()
    if option == 2:
        SpotifyScraper.getAlbums()
    if option == 3:
        SpotifyScraper.getTracks()
    if option == 4:
        SpotifyScraper.getTrackDetails()
    if option == 5:
        Parsers.AiParser.batchCreator()
    if option == 6:
        Parsers.AiParser.queueBatches()
    if option == 7:
        Parsers.AiParser.getBatches()
    if option == 8:
        Parsers.AiParser.handleFinishedBatches()
main()

