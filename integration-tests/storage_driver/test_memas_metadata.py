import pytest
from memas.interface.corpus import CorpusType
from memas.interface.exceptions import NamespaceExistsException
from memas.interface.namespace import ROOT_ID
from memas.storage_driver.memas_metadata import MemasMetadataStoreImpl


metadata = MemasMetadataStoreImpl()


def test_init():
    metadata.init()


def test_create_namespace():
    metadata.init()

    namespace_id = metadata.create_namespace("test_create_namespace", parent_id=ROOT_ID)
    assert metadata._get_id_by_name("test_create_namespace") == namespace_id

    with pytest.raises(NamespaceExistsException):
        namespace_id = metadata.create_namespace("test_create_namespace", parent_id=ROOT_ID)


def test_create_convo_corpus():
    metadata.init()

    namespace_id = metadata.create_namespace("test_create_convo_corpus")
    corpus_id = metadata.create_conversation_corpus("test_create_convo_corpus:convo1")
    corpus_info = metadata.get_corpus_info("test_create_convo_corpus:convo1")
    assert corpus_info.corpus_id == corpus_id
    assert corpus_info.corpus_type == CorpusType.CONVERSATION

    with pytest.raises(NamespaceExistsException):
        metadata.create_conversation_corpus("test_create_convo_corpus:convo1")


def test_create_knowledge_corpus():
    metadata.init()

    namespace_id = metadata.create_namespace("test_create_knowledge_corpus")
    corpus_id = metadata.create_knowledge_corpus("test_create_knowledge_corpus:knowledge1")
    corpus_info = metadata.get_corpus_info("test_create_knowledge_corpus:knowledge1")
    assert corpus_info.corpus_id == corpus_id
    assert corpus_info.corpus_type == CorpusType.KNOWLEDGE

    with pytest.raises(NamespaceExistsException):
        metadata.create_knowledge_corpus("test_create_knowledge_corpus:knowledge1")


def test_get_query_corpora():
    metadata.init()

    namespace_id = metadata.create_namespace("test_get_query_corpora")
    corpus_id1 = metadata.create_conversation_corpus("test_get_query_corpora:knowledge1")
    corpus_id2 = metadata.create_conversation_corpus("test_get_query_corpora:convo1")

    corpora = metadata.get_query_corpora("test_get_query_corpora")
    assert corpora == {corpus_id1, corpus_id2}
