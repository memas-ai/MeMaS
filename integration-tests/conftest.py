import os
import pytest
import yaml
from cassandra.cqlengine import management, connection
from pymilvus import utility
from pymilvus import connections as milvus_connection
from elasticsearch import Elasticsearch
from flask import Flask, Config
from memas.app import create_app
from memas.context_manager import ctx, EnvironmentConstants, read_env
from memas.storage_driver import corpus_doc_store, corpus_vector_store


# TODO: properly create different sets of configs and load them according to scenario

corpus_doc_store.CORPUS_INDEX = "memas-integ-test"
corpus_vector_store.USE_COLLECTION_NAME = "memas_USE_integ_test"


CONFIG_PATH = "../integration-tests/integ-test-config.yml"


def clean_resources():
    config = Config(os.getcwd() + "/memas/")
    config.from_file(CONFIG_PATH, load=yaml.safe_load)
    constants = EnvironmentConstants(config)

    try:
        connection.setup([constants.cassandra_ip], "system", protocol_version=4)
        management.drop_keyspace(constants.cassandra_keyspace)
    except Exception:
        pass

    try:
        milvus_connection.connect("default", host=constants.milvus_ip, port=constants.milvus_port)
        utility.drop_collection(collection_name=corpus_vector_store.USE_COLLECTION_NAME)
        milvus_connection.disconnect("default")
    except Exception:
        pass

    try:
        # TODO: refactor to use https
        es_addr = f"http://{constants.es_ip}:{constants.es_port}"
        es = Elasticsearch(es_addr, basic_auth=("elastic", constants.es_pwd))
        es.indices.delete(index=corpus_doc_store.CORPUS_INDEX)
    except Exception as ignored:
        pass


def create_test_app():
    # clean all existing to ensure a clean run
    clean_resources()

    # first init to setup
    with pytest.raises(SystemExit):
        # Note that first init should exit after initializing. So we need to catch and verify
        create_app(CONFIG_PATH, first_init=True)

    app = create_app(CONFIG_PATH)

    return app


app: Flask = create_test_app()


@pytest.fixture
def test_client():
    yield app.test_client()


@pytest.fixture
def es_client():
    with app.app_context():
        yield ctx.es
