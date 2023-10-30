import pytest
import uuid
from memas.interface.corpus import CorpusInfo, CorpusType
from memas.interface.exceptions import IllegalStateException, NamespaceExistsException, NamespaceDoesNotExistException
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
    assert corpora == {
        CorpusInfo("test_get_query_corpora:knowledge1", namespace_id, corpus_id1, CorpusType.CONVERSATION),
        CorpusInfo("test_get_query_corpora:convo1", namespace_id, corpus_id2, CorpusType.CONVERSATION)
    }


def test_initiate_delete_corpus():
    metadata.init()

    namespace_id = metadata.create_namespace("test_initiate_delete_corpus")
    corpus_pathname = "test_initiate_delete_corpus:convo1"
    corpus_id = metadata.create_conversation_corpus(corpus_pathname)

    corpus_info = metadata.get_corpus_info(corpus_pathname)
    assert corpus_info.corpus_id == corpus_id

    metadata.initiate_delete_corpus(namespace_id, corpus_id, corpus_pathname)

    # since it's not a full delete, we'll still be able to query metadata given the ids
    corpus_info = metadata.get_corpus_info_by_id(namespace_id, corpus_id)
    assert corpus_info.corpus_id == corpus_id

    with pytest.raises(NamespaceDoesNotExistException):
        corpus_info = metadata.get_corpus_info(corpus_pathname)


def test_initiate_delete_wrong_corpus():
    metadata.init()

    namespace_id = metadata.create_namespace("initiate_delete_wrong_corpus")
    corpus_pathname = "initiate_delete_wrong_corpus:convo1"
    corpus_id = metadata.create_conversation_corpus(corpus_pathname)

    corpus_info = metadata.get_corpus_info(corpus_pathname)
    assert corpus_info.corpus_id == corpus_id

    with pytest.raises(NamespaceDoesNotExistException):
        metadata.initiate_delete_corpus(namespace_id, uuid.uuid4(), corpus_pathname)


def test_finish_delete_corpus():
    metadata.init()

    namespace_id = metadata.create_namespace("test_finish_delete_corpus")
    corpus_pathname = "test_finish_delete_corpus:convo1"
    corpus_id = metadata.create_conversation_corpus(corpus_pathname)

    corpus_info = metadata.get_corpus_info_by_id(namespace_id, corpus_id)
    assert corpus_info.corpus_id == corpus_id

    metadata.initiate_delete_corpus(namespace_id, corpus_id, corpus_pathname)
    metadata.finish_delete_corpus(namespace_id, corpus_id)

    with pytest.raises(IllegalStateException):
        metadata.get_corpus_info_by_id(namespace_id, corpus_id)
