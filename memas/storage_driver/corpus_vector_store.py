from dataclasses import dataclass
import logging
import numpy as np
import re
import time
import uuid
from pymilvus import (
    connections,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
)
from memas.encoder.universal_sentence_encoder import USE_VECTOR_DIMENSION, USETextEncoder
from memas.interface.storage_driver import CorpusVectorStore, DocumentEntity
from memas.text_parsing.text_parsers import split_doc


_log = logging.getLogger(__name__)


USE_COLLECTION_NAME = "corpus_USE_sentence_store"


CORPUS_FIELD = "corpus_id"
DOCUMENT_NAME = "document_name"
EMBEDDING_FIELD = "embedding"
START_FIELD = "start_index"
END_FIELD = "end_index"
TEXT_PREVIEW = "text_preview"

MAX_TEXT_LENGTH = 1024


fields = [
    # The first 32 length is the document id, while the later 32 is the sentence id.
    # the sentence id is just used to avoid key collision.
    FieldSchema(name="composite_id", dtype=DataType.VARCHAR,
                max_length=64, is_primary=True, auto_id=False),
    FieldSchema(name=CORPUS_FIELD, dtype=DataType.VARCHAR,
                max_length=32, is_partition_key=True),
    FieldSchema(name=DOCUMENT_NAME, dtype=DataType.VARCHAR,
                max_length=256),
    FieldSchema(name="text_preview", dtype=DataType.VARCHAR, max_length=MAX_TEXT_LENGTH),
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
    document_name: str
    text_preview: str
    embedding: np.ndarray
    start_index: int
    end_index: int

    def to_data(self):
        return [[self.composite_id], [self.corpus_id], [self.document_name], [self.text_preview], self.embedding, [self.start_index], [self.end_index]]


def hash_sentence_id(document_id: uuid.UUID, sentence: str) -> uuid.UUID:
    return uuid.uuid5(document_id, sentence)


def convert_batch(objects: list[USESentenceObject]):
    composite_ids, corpus_ids, document_names, text_previews, embeddings, start_indices, end_indices = [], [], [], [], [], [], []
    for obj in objects:
        composite_ids.append(obj.composite_id)
        corpus_ids.append(obj.corpus_id)
        document_names.append(obj.document_name)
        text_previews.append(obj.text_preview)
        embeddings.append(obj.embedding)
        start_indices.append(obj.start_index)
        end_indices.append(obj.end_index)

    return [composite_ids, corpus_ids, document_names, text_previews, np.row_stack(embeddings), start_indices, end_indices]


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

    def search_corpora(self, corpus_ids: list[uuid.UUID], clue: str) -> list[tuple[float, DocumentEntity, int, int]]:
        _log.debug(f"Searching vectors for [corpus_ids={corpus_ids}]")
        _log.handlers

        vec_search_count = 100
        # Create boolean expression to match all data in the corpus set
        filter_str = ""
        for corpus_id in corpus_ids:
            filter_str += f"{CORPUS_FIELD} == \"{corpus_id.hex}\" ||"

        # Remove last OR
        filter_str = filter_str[:-2]

        clue_split = split_doc(clue, MAX_TEXT_LENGTH)
        result = self.collection.search([x.tolist() for x in self.encoder.embed_multiple(clue_split)], EMBEDDING_FIELD, param={},
                                        limit=vec_search_count, expr=filter_str,
                                        output_fields=[CORPUS_FIELD, START_FIELD, END_FIELD, DOCUMENT_NAME, TEXT_PREVIEW])
        output = []
        for hits in result:
            for hit in hits:
                doc_entity = DocumentEntity(uuid.UUID(hit.entity.corpus_id), uuid.UUID(
                    hit.id[:32]), hit.entity.document_name, hit.entity.text_preview)
                output.append((hit.distance, doc_entity, hit.entity.start_index, hit.entity.end_index))
        return output

    def save_documents(self, doc_entities: list[DocumentEntity]) -> bool:
        _log.debug(f"Saving vectors for [corpus_ids={[x.corpus_id for x in doc_entities]}]")

        insert_count = 0
        sentence_count = 0
        for doc_entity in doc_entities:
            sentences = split_doc(doc_entity.document, MAX_TEXT_LENGTH)
            objects: list[USESentenceObject] = []
            sentence_count = sentence_count + len(sentences)

            doc_embeddings = self.encoder.embed_multiple(sentences)
            start = 0
            index = 0
            for sentence in sentences:
                # deterministically generate the sentence id, so we can later get/delete them
                sentence_id = hash_sentence_id(doc_entity.document_id, sentence)
                composite_id = doc_entity.document_id.hex + sentence_id.hex
                end = start + len(sentence)
                objects.append(USESentenceObject(composite_id, doc_entity.corpus_id.hex, doc_entity.document_name,
                                                 sentence[:MAX_TEXT_LENGTH], doc_embeddings[index], start, end))
                index = index + 1
                start = end

            insert_count = insert_count + self.collection.insert(convert_batch(objects)).insert_count

        return insert_count == sentence_count


SINGLETON: CorpusVectorStore = MilvusUSESentenceVectorStore()
