from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from uuid import UUID


class CorpusType(Enum):
    KNOWLEDGE = "knowledge"
    CONVERSATION = "conversation"


@dataclass
class Citation:
    source_uri: str
    source_name: str
    corpus_name: str
    description: str


@dataclass
class CorpusInfo:
    corpus_pathname: str
    corpus_id: UUID
    corpus_type: CorpusType


class Corpus(ABC):
    """
    Corpus interface used to hide the different implementations
    """

    def __init__(self, corpus_id: UUID, corpus_name: str):
        self.corpus_id = corpus_id
        self.corpus_name = corpus_name

    @abstractmethod
    def store_and_index(self, document: str, document_name: str, citation: Citation) -> bool:
        """Store and index a "document"

        Args:
            document (str): text block we want to store
            citation (Citation): citation of the "document"

        Returns:
            bool: success or not
        """

    @abstractmethod
    def search(self, clue: str) -> list[tuple[float, str, Citation]]:
        """Search for (document,citation) pairs related to the clue

        Args:
            clue (str): chat query to search for

        Returns:
            list[tuple[str, Citation]]: a list of (document, citation) pairs
        """

    @abstractmethod
    def generate_search_instructions(self, clue: str) -> any:
        """Generates batchable search instructions, used for multi corpus queries. TODO: decide instructions format

        Args:
            clue (str): _description_

        Returns:
            any: _description_
        """


class CorpusFactory(ABC):
    @abstractmethod
    def produce(self, corpus_id: UUID):
        # FIXME: do we want to pass in any arguments?
        pass
