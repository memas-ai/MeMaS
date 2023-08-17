import tensorflow_hub as hub
import tensorflow as tf
import numpy as np
from memas.interface.encoder import TextEncoder
import random


# @param ["https://tfhub.dev/google/universal-sentence-encoder/4",
#   "https://tfhub.dev/google/universal-sentence-encoder-large/5"]
USE_LOCAL_MODEL_URL = "encoder/universal-sentence-encoder_4"


USE_VECTOR_DIMENSION = 512


class USETextEncoder(TextEncoder):
    def __init__(self, model_url: str = USE_LOCAL_MODEL_URL) -> None:
        super().__init__()
        self.model_url: str = model_url

    def init(self):
        self.encoder = hub.load(self.model_url)

    def embed(self, text: str) -> np.ndarray:
        return self.encoder(text).numpy()

    def embed_multiple(self, text_list: list[str]) -> list[np.ndarray]:
        return [x.numpy() for x in self.encoder(text_list)]
