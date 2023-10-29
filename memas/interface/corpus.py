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
    document_name: str


@dataclass
class CorpusInfo:
    corpus_pathname: str
    namespace_id: UUID
    corpus_id: UUID
    corpus_type: CorpusType

    def __hash__(self) -> int:
        return hash((self.namespace_id, self.corpus_id, self.corpus_pathname))


class Corpus(ABC):
    """
    Corpus interface used to access data within the corpus, and hide the different implementations
    """

    def __init__(self, corpus_info: CorpusInfo):
        self.corpus_id: UUID = corpus_info.corpus_id
        self.corpus_info: CorpusInfo = corpus_info

    @abstractmethod
    def store_and_index(self, document: str, citation: Citation) -> bool:
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
    def delete_all_content(self):
        """Deletes all data in the corpus
        """


class CorpusFactory(ABC):
    @abstractmethod
    def produce(self, corpus_info: CorpusInfo):
        # FIXME: do we want to pass in any arguments?
        pass
