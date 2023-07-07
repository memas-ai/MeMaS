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
