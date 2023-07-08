import uuid
from dataclasses import dataclass
import numpy as np
from pymilvus import (
    connections,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
)
from memas.encoder.universal_sentence_encoder import USE_VECTOR_DIMENSION, USETextEncoder
from memas.interface.encoder import TextEncoder
from memas.interface.storage_driver import CorpusVectorStore, DocumentEntity


USE_COLLECTION_NAME = "corpus-USE-sentence-store"


CORPUS_FIELD = "corpus_id"
EMBEDDING_FIELD = "embedding"
START_FIELD = "start_index"
END_FIELD = "end_index"


fields = [
    # The first 32 length is the document id, while the later 32 is the sentence id.
    # the sentence id is just used to avoid key collision.
    FieldSchema(name="composite_id", dtype=DataType.VARCHAR,
                max_length=64, is_primary=True, auto_id=False),
    FieldSchema(name=CORPUS_FIELD, dtype=DataType.VARCHAR,
                max_length=32, is_partition_key=True),
    FieldSchema(name="text_preview", dtype=DataType.VARCHAR, max_length=32),
    FieldSchema(name=EMBEDDING_FIELD, dtype=DataType.FLOAT_VECTOR, dim=USE_VECTOR_DIMENSION),
    FieldSchema(name=START_FIELD, dtype=DataType.INT64),
    FieldSchema(name=END_FIELD, dtype=DataType.INT64),
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


def hash_sentence_id(document_id: uuid.UUID, sentence: str) -> uuid.UUID:
    return uuid.uuid5(document_id, sentence)


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


class MilvusUSESentenceVectorStore(CorpusVectorStore):
    def __init__(self) -> None:
        super().__init__(USETextEncoder())
        self.collection: Collection

    def first_init(self):
        self.collection: Collection = Collection(USE_COLLECTION_NAME, sentance_schema)
        index = {
            "index_type": "FLAT",
            "metric_type": "L2",
            "params": {},
        }
        self.collection.create_index(EMBEDDING_FIELD, index)
        self.collection.load()
        self.encoder.init()

    def init(self):
        self.collection: Collection = Collection(USE_COLLECTION_NAME, sentance_schema)
        self.collection.load()
        self.encoder.init()

    def search(self, corpus_id: uuid.UUID, clue: str) -> list[tuple[float, uuid.UUID, uuid.UUID]]:
        result = self.collection.search(self.encoder.embed([clue]).tolist(), EMBEDDING_FIELD, param={},
                                        limit=10, expr=f"{CORPUS_FIELD} == \"{corpus_id.hex}\"",
                                        output_fields=[CORPUS_FIELD, START_FIELD, END_FIELD])
        output = []
        for hits in result:
            for hit in hits:
                output.append((hit.distance, uuid.UUID(hit.entity.corpus_id), uuid.UUID(hit.id[:32])))
        return output

    def split_doc(self, document: str) -> list[str]:
        # TODO: implement something proper
        return list(filter(lambda x: x != "", document.split(". ")))

    def save_document(self, doc_entity: DocumentEntity):
        sentences = self.split_doc(doc_entity.document)
        objects: list[USESentenceObject] = []

        start = 0
        for sentence in sentences:
            # deterministically generate the sentence id, so we can later get/delete them
            sentence_id = hash_sentence_id(doc_entity.document_id, sentence)
            composite_id = doc_entity.document_id.hex + sentence_id.hex
            end = start + len(sentence)
            objects.append(USESentenceObject(composite_id, doc_entity.corpus_id.hex,
                           sentence[:32], self.encoder.embed([sentence]), start, end))

            start = end

        self.collection.insert(convert_batch(objects))
