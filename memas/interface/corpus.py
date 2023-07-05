from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class Citation:
    source_uri: str
    source_name: str
    description: str


class Corpus(ABC):
    """
    Corpus interface used to hide the different implementations
    """
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
    def search(self, clue: str) -> list[tuple[str, Citation]]:
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