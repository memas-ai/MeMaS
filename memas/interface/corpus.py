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
    def store_and_index(self, document: str):
        pass

    @abstractmethod
    def search(self, clue: str) -> list[tuple[str, Citation]]:
        pass

    @abstractmethod
    def generate_search_instructions(self, clue: str) -> any:
        """Generates batchable search instructions, used for multi corpus queries. TODO: decide instructions format

        Args:
            clue (str): _description_

        Returns:
            any: _description_
        """
        pass
