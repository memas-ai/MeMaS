import pytest
from cassandra.cqlengine import management, connection
from pymilvus import utility
from memas.context_manager import ctx
from memas.storage_driver import corpus_doc_store, corpus_vector_store


# TODO: properly create different sets of configs and load them according to scenario

corpus_doc_store.CORPUS_INDEX = "memas-integ-test"
corpus_vector_store.USE_COLLECTION_NAME = "memas_USE_integ_test"


@pytest.fixture
def es_client():
    print("Initializing es client fixture")
    ctx.init_clients()
    yield ctx.es


@pytest.fixture
def cassandra_client():
    # TODO: refactor this montrosity :D
    connection.setup(['127.0.0.1'], "system", protocol_version=4)
    management.drop_keyspace("memas_integ_test")
    ctx.consts.cassandra_keyspace = "memas_integ_test"
    print("Created a clean cassandra keyspace")
    ctx.first_init()
    ctx.init_clients()
    yield ctx


@pytest.fixture
def clean_milvus():
    ctx.init_clients()

    utility.drop_collection(collection_name="memas_USE_integ_test")
    yield ctx
