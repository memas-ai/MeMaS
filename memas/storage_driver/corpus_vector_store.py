import uuid
from dataclasses import dataclass
import numpy as np
import tensorflow_hub as hub
from pymilvus import (
    connections,
    utility,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
)
from memas.interface.storage_driver import CorpusVectorStore


CORPUS_FIELD = "corpus_id"
EMBEDDING_FIELD = "embedding"


fields = [
    # The first 32 length is the document id, while the later 32 is the sentence id.
    # the sentence id is just used to avoid key collision.
    FieldSchema(name="composite_id", dtype=DataType.VARCHAR,
                max_length=64, is_primary=True, auto_id=False),
    FieldSchema(name=CORPUS_FIELD, dtype=DataType.VARCHAR,
                max_length=32, is_partition_key=True),
    FieldSchema(name="text_preview", dtype=DataType.VARCHAR, max_length=32),
    FieldSchema(name=EMBEDDING_FIELD, dtype=DataType.FLOAT_VECTOR, dim=512),
    FieldSchema(name="start_index", dtype=DataType.INT64),
    FieldSchema(name="end_index", dtype=DataType.INT64),
]
sentance_schema = CollectionSchema(
    fields, "Corpus Vector Table for storing Universal Sentence Encoder embeddings")


@dataclass
class USESentenceObject:
    composite_id: str
    corpus_id: str
    text_preview: str
    embedding: np.ndarray
    start_index: int
    end_index: int

    def to_data(self):
        return [[self.composite_id], [self.corpus_id], [self.text_preview], self.embedding, [self.start_index], [self.end_index]]


def convert_batch(objects: list[USESentenceObject]):
    composite_ids, corpus_ids, text_previews, embeddings, start_indices, end_indices = [], [], [], [], [], []
    for obj in objects:
        composite_ids.append(obj.composite_id)
        corpus_ids.append(obj.corpus_id)
        text_previews.append(obj.text_preview)
        embeddings.append(obj.embedding) 
        start_indices.append(obj.start_index)
        end_indices.append(obj.end_index)
    
    return [composite_ids, corpus_ids, text_previews, np.row_stack(embeddings), start_indices, end_indices]


# @param ["https://tfhub.dev/google/universal-sentence-encoder/4",
#   "https://tfhub.dev/google/universal-sentence-encoder-large/5"]
USE_module_url = "encoder/universal-sentence-encoder_4"


USE_COLLECTION_NAME = "corpus-USE-sentence-store"


class MilvusUSESentenceVectorStore(CorpusVectorStore):
    def __init__(self) -> None:
        super().__init__()
        self.collection: Collection
        self.encoder = hub.load(USE_module_url)

    def _embed(self, vec) -> np.ndarray:
        return self.encoder(vec).numpy()

    def first_init(self):
        self.collection: Collection = Collection(USE_COLLECTION_NAME, sentance_schema)
        index = {
            "index_type": "FLAT",
            "metric_type": "L2",
            "params": {},
        }
        self.collection.create_index(EMBEDDING_FIELD, index)
        self.collection.load()

    def init(self):
        self.collection: Collection = Collection(USE_COLLECTION_NAME, sentance_schema)
        self.collection.load()

    def search(self, corpus_id: uuid.UUID, clue: str):
        result = self.collection.search(self._embed([clue]).tolist(), EMBEDDING_FIELD, param={},
                                        limit=10, expr=f"{CORPUS_FIELD} == \"{corpus_id.hex}\"")
        return result

    def split_doc(self, document: str) -> list[str]:
        # TODO: implement something proper
        # return list(filter(lambda x: x != "", document.split(". ")))
        return document.split(". ")

    def save_document(self, corpus_id: uuid.UUID, document_id: uuid.UUID, document: str):        
        sentences = self.split_doc(document)
        objects: list[USESentenceObject] = []

        start = 0
        for sentence in sentences:
            sentence_id = uuid.uuid4()
            composite_id = document_id.hex + sentence_id.hex
            end = start + len(sentence)
            objects.append(USESentenceObject(composite_id, corpus_id.hex, sentence[:32], self._embed([sentence]), start, end))

            start = end

        self.collection.insert(convert_batch(objects))
