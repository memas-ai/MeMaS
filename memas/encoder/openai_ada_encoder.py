import numpy as np
import openai
from memas.interface.encoder import TextEncoder


ADA_MODEL="text-embedding-ada-002"


class ADATextEncoder(TextEncoder):
    def __init__(self, api_key) -> None:
        super().__init__(ENCODER_NAME="ADA", VECTOR_DIMENSION=1536)
        openai.api_key = api_key

    def init(self):
        pass

    def embed(self, text: str) -> np.ndarray:
        return np.array(openai.Embedding.create(input = [text], model=ADA_MODEL)['data'][0]['embedding'])

    def embed_multiple(self, text_list: list[str]) -> list[np.ndarray]:
        embeddings = openai.Embedding.create(input = text_list, model=ADA_MODEL)['data']
        return [np.array(resp['embedding']) for resp in embeddings]
