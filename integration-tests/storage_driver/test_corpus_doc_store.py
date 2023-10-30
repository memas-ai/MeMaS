import pytest
from elasticsearch import Elasticsearch
from memas.context_manager import ContextManager
from memas.storage_driver import corpus_doc_store
from memas.interface.storage_driver import DocumentEntity
import uuid
import time


def test_init(ctx: ContextManager):
    doc_store = corpus_doc_store.ESDocumentStore(ctx.es)
    doc_store.init()


def test_save_then_search(ctx: ContextManager):
    doc_store = corpus_doc_store.ESDocumentStore(ctx.es)
    doc_store.init()

    corpus_id1 = uuid.uuid1()
    corpus_id2 = uuid.uuid4()

    document_id1 = uuid.uuid4()
    document_id2 = uuid.uuid4()
    document_id3 = uuid.uuid4()

    chunk_id1 = document_id1.hex + '{:032b}'.format(0)
    chunk_id2 = document_id2.hex + '{:032b}'.format(0)
    chunk_id3 = document_id3.hex + '{:032b}'.format(0)

    assert doc_store.save_documents([(chunk_id1, DocumentEntity(
        corpus_id1, document_id1, "test1", "MeMaS is great and easy to use"))])
    assert doc_store.save_documents([(chunk_id2, DocumentEntity(
        corpus_id2, document_id2, "test2", "MeMaS is coded in python and is horrible"))])
    assert doc_store.save_documents([(chunk_id3, DocumentEntity(
        corpus_id1, document_id3, "test3", "Memory Management System"))])

    time.sleep(2)

    result = doc_store.search_corpora([corpus_id1], "memas is horrible")

    # check that we only found document 1
    assert len(result) == 1
    assert result[0][1].document_id == document_id1

    # check that the score is reasonable
    assert result[0][0] > 0
