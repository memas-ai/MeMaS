import pytest
from elasticsearch import Elasticsearch
from memas.context_manager import ContextManager
from memas.storage_driver import corpus_doc_store
from memas.interface.storage_driver import DocumentEntity
import uuid
import time

# Override the corpus index so that integration tests run on a different index
corpus_doc_store.CORPUS_INDEX = "memas-integ-test"


def test_init(es_client: Elasticsearch):
    # clean the index for reliable testing
    try:
        es_client.indices.delete(index="memas-integ-test")
    except Exception as ignored:
        pass

    doc_store = corpus_doc_store.ESDocumentStore(es_client)

    assert doc_store.init()


def test_save_then_search(es_client):
    doc_store = corpus_doc_store.ESDocumentStore(es_client)

    corpus_id1 = uuid.uuid1()
    corpus_id2 = uuid.uuid4()

    document_id1 = uuid.uuid4()
    document_id2 = uuid.uuid4()
    document_id3 = uuid.uuid4()

    assert doc_store.save_document(DocumentEntity(
        corpus_id1, document_id1, "test1", "MeMaS is great and easy to use"))
    assert doc_store.save_document(DocumentEntity(
        corpus_id2, document_id2, "test2", "MeMaS is coded in python and is horrible"))
    assert doc_store.save_document(DocumentEntity(
        corpus_id1, document_id3, "test3", "Memory Management System"))

    time.sleep(2)

    result = doc_store.search_corpus(corpus_id1, "memas is horrible")

    # check that we only found document 1
    assert len(result) == 1
    assert result[0][1].document_id == document_id1

    # check that the score is reasonable
    assert result[0][0] > 0
