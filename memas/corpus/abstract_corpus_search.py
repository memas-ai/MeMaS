from abc import ABC, abstractmethod
from search_redirect import SearchSettings
from uuid import UUID


class CorpusSearch(ABC):
    def __init__(self, corpus_ID : UUID, corpus_name : str):
        self.corpus_ID = corpus_ID
        self.corpus_name = corpus_name

    @abstractmethod
    def init(self):
        """Initialize the encoder
        """

    @abstractmethod
    def search(self, corpusID : UUID, clue: str, searchSettings :  SearchSettings) -> str:
        """Embed the corpus with corpusID for the best matches 

        Args:
            clue (str): the text to find matches with

        Returns:
            str: the desired text that was fetched from corpusID in conformance with the searchSettings
        """
