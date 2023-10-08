import os
from dataclasses import dataclass
import logging
from werkzeug.local import LocalProxy
from flask import current_app, Config
from cassandra.cluster import Cluster, Session
from cassandra.cqlengine import connection as c_connection
from elasticsearch import Elasticsearch
from pymilvus import connections as milvus_connection
from memas.encoder.universal_sentence_encoder import USETextEncoder
from memas.interface.exceptions import IllegalStateException
from memas.interface.storage_driver import CorpusDocumentMetadataStore, CorpusDocumentStore, CorpusVectorStore, MemasMetadataStore
from memas.storage_driver import corpus_doc_metadata, corpus_doc_store, corpus_vector_store, memas_metadata
from memas.corpus.corpus_provider import CorpusProvider


_log = logging.getLogger(__name__)


def read_env(name: str, default: str = None) -> str:
    val = os.environ.get(name)
    if not val:
        if not default:
            raise ValueError(f"Environment Variable '{name}' is not set.")
        return default
    return val


# TODO: properly enable frozen with @dataclass(frozen=True)
@dataclass
class EnvironmentConstants:
    cassandra_ip: str
    cassandra_port: int
    cassandra_keyspace: str
    cassandra_replication_factor: int

    es_ip: str
    es_port: int
    es_pwd: str

    milvus_ip: str
    milvus_port: int

    def __init__(self, app_config: Config):
        cassandra_configs = app_config["CASSANDRA"]
        self.cassandra_ip = cassandra_configs["ip"]
        self.cassandra_port = cassandra_configs["port"]
        self.cassandra_keyspace = cassandra_configs["keyspace"]
        self.cassandra_replication_factor = cassandra_configs["replication_factor"]

        es_configs = app_config["ELASTICSEARCH"]
        self.es_ip = es_configs["ip"]
        self.es_port = es_configs["port"]
        self.es_pwd = read_env("ELASTIC_PASSWORD")

        milvus_configs = app_config["MILVUS"]
        self.milvus_ip = milvus_configs["ip"]
        self.milvus_port = milvus_configs["port"]


class ContextManager:
    def __init__(self, app_config: Config):
        self.consts: EnvironmentConstants = EnvironmentConstants(app_config)

        # Data Stores
        self.memas_metadata: MemasMetadataStore = memas_metadata.SINGLETON
        self.corpus_metadata: CorpusDocumentMetadataStore = corpus_doc_metadata.SINGLETON
        self.corpus_vec: CorpusVectorStore = corpus_vector_store.MilvusSentenceVectorStore(USETextEncoder())
        self.corpus_doc: CorpusDocumentStore

        # clients
        self.es: Elasticsearch

        # Corpus provider
        self.corpus_provider: CorpusProvider

    def setup_cassandra_keyspace(self):
        """Setup the cassandra keyspace. We only want to run the very first server launch. 
        """
        cassandra_cluster: Cluster = Cluster(
            [self.consts.cassandra_ip], port=self.consts.cassandra_port, protocol_version=4)
        session: Session = cassandra_cluster.connect()

        replication_options = {
            'class': 'SimpleStrategy',
            'replication_factor': self.consts.cassandra_replication_factor
        }
        # NOTE: management.create_keyspace_simple doesn't work when we don't have a single keyspace...
        create_keyspace_query = f"CREATE KEYSPACE {self.consts.cassandra_keyspace} WITH replication = {replication_options};"
        session.execute(create_keyspace_query)
        session.shutdown()

    def init_clients(self) -> None:
        # connect to cassandra
        c_connection.setup([self.consts.cassandra_ip], self.consts.cassandra_keyspace, protocol_version=4)

        # TODO: properly support https
        # connect to elastic search
        es_addr = f"http://{self.consts.es_ip}:{self.consts.es_port}"
        self.es = Elasticsearch(es_addr, basic_auth=("elastic", self.consts.es_pwd))

        # connect to milvus
        milvus_connection.connect("default", host=self.consts.milvus_ip, port=self.consts.milvus_port)

    def first_init_datastores(self) -> None:
        if self.es is None:
            raise IllegalStateException("Attempted to initialize data stores before connectors/clients")
        self.corpus_doc = corpus_doc_store.ESDocumentStore(self.es)

        self.memas_metadata.first_init()
        self.corpus_metadata.first_init()
        self.corpus_vec.first_init()
        self.corpus_doc.first_init()

    def init_datastores(self) -> None:
        if self.es is None:
            raise IllegalStateException("Attempted to initialize data stores before connectors/clients")
        self.corpus_doc = corpus_doc_store.ESDocumentStore(self.es)

        self.memas_metadata.init()
        self.corpus_metadata.init()
        self.corpus_vec.init()
        self.corpus_doc.init()

        self.corpus_provider = CorpusProvider(self.corpus_metadata, self.corpus_doc, self.corpus_vec)

    def init(self) -> None:
        self.init_clients()
        self.init_datastores()

    def first_init(self) -> None:
        """Init function used only for initializing the first time
        """
        self.setup_cassandra_keyspace()
        self.init_clients()
        self.first_init_datastores()
        self.shutdown()

    def shutdown(self) -> None:
        self.es.close()
        milvus_connection.disconnect("default")
        c_connection.unregister_connection("default")


def get_ctx():
    return current_app.ctx


ctx: ContextManager = LocalProxy(get_ctx)
