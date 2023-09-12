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
    async def store_and_index(self, doc_name_text_cit_triples : list[tuple[str, str, Citation]]) -> bool:
        """Store and index a list of "document tuples (document_name : str, docuument_text : str, citation : Citation)"

        Args:
            doc_name_text_cit_triples list[tuple[str, str, Citation]] : list of tuples where each tuple is (document_name, document_text, Citation)

        Returns:
            bool: success or not
        """

    @abstractmethod
    def search(self, clue: str) -> list[tuple[str, Citation]]:
        """Search for (document,citation) pairs related to the clue

        Args:
            clue (str): chat query to search for

        Returns:
            list[tuple[str, Citation]]: a list of (document, citation) pairs
        """


class CorpusFactory(ABC):
    @abstractmethod
    def produce(self, corpus_id: UUID):
        # FIXME: do we want to pass in any arguments?
        pass
