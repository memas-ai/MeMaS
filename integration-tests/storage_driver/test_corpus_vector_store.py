import numpy as np
import uuid
import time
from memas.interface.storage_driver import DocumentEntity
from memas.storage_driver.corpus_vector_store import MilvusUSESentenceVectorStore


def test_init(clean_milvus):
    store = MilvusUSESentenceVectorStore()
    store.first_init()


def test_save_then_search(clean_milvus):
    store = MilvusUSESentenceVectorStore()
    store.first_init()

    corpus_id1 = uuid.uuid4()
    corpus_id2 = uuid.uuid4()
    document_id1 = uuid.uuid4()
    document_id2 = uuid.uuid4()
    document_id3 = uuid.uuid4()

    store.save_document(DocumentEntity(corpus_id1, document_id1, "doc1",
                        "The sun is high. California sunshine is great. "))
    store.save_document(DocumentEntity(corpus_id1, document_id2, "doc2",
                        "I picked up my phone and then dropped it again"))
    store.save_document(DocumentEntity(corpus_id2, document_id3, "doc3", "The weather is great today"))
    time.sleep(1)

    result = store.search(corpus_id1, "How's the weather today?")
    assert result[0][1] == corpus_id1
    assert document_id3 not in {t[2] for t in result}
