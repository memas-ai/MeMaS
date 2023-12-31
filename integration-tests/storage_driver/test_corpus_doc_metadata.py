import pytest
import uuid
from memas.interface.corpus import Citation
from memas.interface.exceptions import DocumentMetadataNotFound
from memas.storage_driver.corpus_doc_metadata import CorpusDocumentMetadataStoreImpl


metadata = CorpusDocumentMetadataStoreImpl()


def test_init():
    metadata.init()


def test_insert_and_get():
    corpus_id = uuid.uuid4()
    document_id = uuid.uuid4()

    citation = Citation("google.com", "test google", "just a simple test", "test")
    metadata.insert_document_metadata(corpus_id, document_id, 1, citation)
    assert metadata.get_document_citation(corpus_id, document_id) == citation


def test_delete_corpus():
    corpus_id = uuid.uuid4()
    document_id = uuid.uuid4()

    citation = Citation("google.com", "test google", "just a simple test", "test")
    metadata.insert_document_metadata(corpus_id, document_id, 1, citation)
    metadata.delete_corpus(corpus_id)

    with pytest.raises(DocumentMetadataNotFound):
        metadata.get_document_citation(corpus_id, document_id)
