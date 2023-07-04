import os
from dataclasses import dataclass
from cassandra.cluster import Cluster, Session
from cassandra.cqlengine import connection
from elasticsearch import Elasticsearch
from pymilvus import connections
from memas.interface.storage_driver import MemasMetadataStore
from memas.storage_driver import memas_metadata


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

    def __init__(self):
        self.cassandra_ip = "127.0.0.1"
        self.cassandra_port = 9042
        self.cassandra_keyspace = "memas"
        self.cassandra_replication_factor = 1

        self.es_ip = "127.0.0.1"
        self.es_port = int(read_env("ES_PORT", 9200))
        self.es_pwd = read_env("ELASTIC_PASSWORD")

        self.milvus_ip = "127.0.0.1"
        self.milvus_port = "19530"


class ContextManager:
    def __init__(self):
        self.consts: EnvironmentConstants = EnvironmentConstants()
        self.memas_metadata: MemasMetadataStore
        self.es: Elasticsearch

    def first_init(self):
        """This is used to run init operations we only want to run the very first server launch. 
        TODO: refactor this entire mess...
        """
        cassandra_cluster: Cluster = Cluster(
            [self.consts.cassandra_ip], port=self.consts.cassandra_port, protocol_version=4)
        session: Session = cassandra_cluster.connect()

        replication_options = {
            'class': 'SimpleStrategy',
            'replication_factor': self.consts.cassandra_replication_factor
        }
        # NOTE: management.create_keyspace_simple doesn't work when we don't have a single keyspace...
        create_keyspace_query = f"CREATE KEYSPACE IF NOT EXISTS {self.consts.cassandra_keyspace} WITH replication = {replication_options};"
        session.execute(create_keyspace_query)
        # session.set_keyspace(self.consts.cassandra_keyspace)
        # connection.register_connection(
        #     "default", session=self.cassandra, default=True)

    def init_clients(self) -> None:
        # connect to cassandra
        connection.setup(
            ['127.0.0.1'], self.consts.cassandra_keyspace, protocol_version=4)

        # TODO: properly support https
        # connect to elastic search
        es_addr = f"http://{self.consts.es_ip}:{self.consts.es_port}"
        self.es = Elasticsearch(es_addr, basic_auth=(
            "elastic", self.consts.es_pwd))

        # connect to milvus
        connections.connect("memas", host=self.consts.milvus_ip,
                            port=self.consts.milvus_port)

    def init_datastores(self) -> None:
        self.memas_metadata = memas_metadata.SINGLETON

    def init(self) -> None:
        self.init_clients()
        self.init_datastores()


ctx: ContextManager = ContextManager()
