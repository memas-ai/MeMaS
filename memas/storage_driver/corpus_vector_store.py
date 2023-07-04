from uuid import UUID
import tensorflow as tf
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
    FieldSchema(name="corpus_id", dtype=DataType.VARCHAR,
                max_length=32, is_partition_key=True),
    FieldSchema(name="text_preview", dtype=DataType.VARCHAR, max_length=32),
    FieldSchema(name=EMBEDDING_FIELD, dtype=DataType.FLOAT_VECTOR, dim=512),
    FieldSchema(name="start_index", dtype=DataType.INT32),
    FieldSchema(name="end_index", dtype=DataType.INT32),
]
sentance_schema = CollectionSchema(
    fields, "Corpus Vector Table for storing Universal Sentence Encoder embeddings")


# @param ["https://tfhub.dev/google/universal-sentence-encoder/4",
#   "https://tfhub.dev/google/universal-sentence-encoder-large/5"]
USE_module_url = "encoder/universal-sentence-encoder_4"


class MilvusUSESentenceVectorStore(CorpusVectorStore):
    def __init__(self) -> None:
        super().__init__()
        self.collection: Collection
        self.encoder = hub.load(USE_module_url)

    def _embed(self, vec):
        return self.encoder(vec).numpy()

    def first_init(self):
        self.collection: Collection = Collection(
            "corpus-USE-sentence-store", sentance_schema)
        index = {
            "index_type": "FLAT",
            "metric_type": "L2",
            "params": {},
        }
        self.collection.create_index(EMBEDDING_FIELD, index)

    def init(self):
        self.collection: Collection = Collection(
            "corpus-USE-sentence-store", sentance_schema)
        self.collection.load()

    def search(self, corpus_id: UUID, clue: str):
        result = self.collection.search(self._embed([clue]).tolist(), EMBEDDING_FIELD, param={},
                                        limit=10, expr=f"{CORPUS_FIELD} == '{corpus_id.hex}'")
        print(result)
