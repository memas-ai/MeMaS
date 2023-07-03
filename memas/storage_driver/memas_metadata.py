from typing import Final
from enum import Enum
import uuid
from datetime import datetime
from cassandra.cqlengine import columns, management
from cassandra.cqlengine.models import Model
from cassandra.cqlengine.query import BatchQuery, LWTException
from memas.interface.exceptions import NamespaceExistsException
from memas.interface.namespace import ROOT_ID, ROOT_NAME, NAMESPACE_SEPARATOR, CORPUS_SEPARATOR, is_pathname_format_valid, is_name_format_valid
from memas.interface.storage_driver import MemasMetadataStore


MAX_PATH_LENGTH: Final[int] = 256
MAX_SEGMENT_LENGTH: Final[int] = 32
# -1 for "." separators
MAX_NS_NAME_LENGTH: Final[int] = MAX_SEGMENT_LENGTH - 1
# -1 for ":" separator
MAX_CORPUS_NAME_LENGTH: Final[int] = MAX_SEGMENT_LENGTH - 1


class CorpusType(Enum):
    KNOWLEDGE = "KNOWLEDGE"
    CONVERSATION = "CONVO"


STD_READ_PERMISSION: Final[int] = 1
STD_WRITE_PERMISSION: Final[int] = 2
READ_AND_WRITE: Final[int] = STD_READ_PERMISSION & STD_WRITE_PERMISSION


class NamespaceNameToId(Model):
    fullname = columns.Ascii(partition_key=True, max_length=MAX_PATH_LENGTH)
    id = columns.UUID(required=True)


class NamespaceParent(Model):
    child_id = columns.UUID(partition_key=True)
    parent_id = columns.UUID(required=True)


# With current schemas, rename will be really hard to support. But if we switch to IDs, things would take at least double the queries.
class NamespaceInfo(Model):
    parent_id = columns.UUID(partition_key=True)
    namespace_id = columns.UUID(primary_key=True)

    parent_path = columns.Ascii(
        required=True, max_length=MAX_PATH_LENGTH - MAX_SEGMENT_LENGTH, min_length=0)
    namespace_name = columns.Ascii(
        required=True, max_length=MAX_NS_NAME_LENGTH)
    # depth = columns.Integer(required=True)
    query_default_corpus = columns.Set(columns.UUID, default=set())
    created_at = columns.DateTime(required=True)


class CorpusInfo(Model):
    parent_id = columns.UUID(partition_key=True)
    corpus_id = columns.UUID(primary_key=True)

    corpus_name = columns.Ascii(
        required=True, max_length=MAX_CORPUS_NAME_LENGTH)
    corpus_type = columns.Ascii(required=True)
    permissions = columns.Integer(required=True)
    created_at = columns.DateTime(required=True)


def parse_pathname(pathname: str) -> tuple[str, str]:
    tokens = pathname.rsplit(NAMESPACE_SEPARATOR, 1)
    if len(tokens) == 1:
        return (ROOT_NAME, pathname)
    return (tokens[0], tokens[1])


class MemasMetadataStoreImpl(MemasMetadataStore):
    def init(self):
        management.sync_table(NamespaceNameToId)
        management.sync_table(NamespaceParent)
        management.sync_table(NamespaceInfo)
        management.sync_table(CorpusInfo)

    def _get_id_by_name(self, fullname: str) -> uuid.UUID:
        if fullname == ROOT_NAME:
            return ROOT_ID
        result = NamespaceNameToId.get(fullname=fullname)
        return result.id

    def _get_ids_by_name(self, fullname: str) -> tuple[uuid.UUID, uuid.UUID]:
        parent_pathname, child_name = parse_pathname(fullname)
        # if parent is root
        if parent_pathname == ROOT_NAME:
            child_id = NamespaceNameToId.get(fullname=fullname).id
            return (ROOT_ID, child_id)

        with BatchQuery() as b:
            child_result = NamespaceInfo.batch(b).get(fullname=fullname)
            parent_result = NamespaceInfo.batch(
                b).get(fullname=parent_pathname)
        return (parent_result.id, child_result.id)

    def create_namespace(self, namespace_pathname: str, *, parent_id: uuid.UUID = None) -> uuid.UUID:
        parent_pathname, child_name = parse_pathname(namespace_pathname)
        if parent_id is None:
            parent_id = self._get_id_by_name(parent_pathname)

        namespace_id = uuid.uuid4()
        now = datetime.now()
        try:
            NamespaceNameToId.if_not_exists().create(
                fullname=namespace_pathname, id=namespace_id)
        except LWTException as ignored:
            raise NamespaceExistsException(namespace_pathname) from ignored

        # FIXME: Currently we don't handle the possibility of namespace ids colliding.
        #   On one hand this probability is extremely low; in our current state we don't expect
        #       a huge number of users
        #   On the other hand, this is costly to handle properly; if we were to separate this
        #       batch query into two queries, we increase the risk of interruptions
        with BatchQuery() as b:
            NamespaceInfo.batch(b).create(parent_id=parent_id, namespace_id=namespace_id,
                                          parent_path=parent_pathname, namespace_name=child_name, created_at=now)
            NamespaceParent.batch(b).create(
                child_id=namespace_id, parent_id=parent_id)

        return namespace_id

    def create_corpus(self, parent_pathname: str, corpus_name: str, corpus_type: CorpusType, permissions: int, *, parent_id: uuid.UUID = None) -> uuid.UUID:
        corpus_pathname = parent_pathname + CORPUS_SEPARATOR + corpus_name
        if parent_id is None:
            parent_id = self._get_id_by_name(parent_pathname)

        corpus_id = uuid.uuid4()
        now = datetime.now()
        try:
            NamespaceNameToId.if_not_exists().create(
                fullname=corpus_pathname, id=corpus_id)
        except LWTException as ignored:
            raise NamespaceExistsException(corpus_pathname) from ignored

        # FIXME: Same issue with namespace id colliding.
        with BatchQuery() as b:
            CorpusInfo.batch(b).create(parent_id=parent_id, corpus_id=corpus_id,
                                       corpus_name=corpus_name, corpus_type=str(corpus_type), permissions=permissions, created_at=now)
            NamespaceParent.batch(b).create(
                child_id=corpus_id, parent_id=parent_id)
        return corpus_id

    def create_conversation_corpus(self, parent_pathname, corpus_name):
        self.create_corpus(parent_pathname=parent_pathname, corpus_name=corpus_name,
                           corpus_type=CorpusType.CONVERSATION, permissions=READ_AND_WRITE)

    def create_knowledge_corpus(self, parent_pathname, corpus_name):
        self.create_corpus(parent_pathname=parent_pathname, corpus_name=corpus_name,
                           corpus_type=CorpusType.KNOWLEDGE, permissions=STD_READ_PERMISSION)


SINGLETON: MemasMetadataStore = MemasMetadataStoreImpl()
