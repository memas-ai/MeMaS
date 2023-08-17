from abc import ABC, abstractmethod
import numpy


class TextEncoder(ABC):
    @abstractmethod
    def init(self):
        """Initialize the encoder
        """

    @abstractmethod
    def embed(self, text: str) -> numpy.ndarray:
        """Embed the supplied text

        Args:
            text (str): the desired text

        Returns:
            numpy.ndarray: embedding
        """
    
    @abstractmethod
    def embed_multiple(self, text_list: list[str]) -> list[numpy.ndarray]:
        """Embed each string of supplied text

        Args:
            text_list (list[str]): the set of desired text to embed

        Returns:
            list of numpy.ndarray: embeddings
        """
