from datetime import datetime
import logging
from typing import Final
import uuid
from cassandra.cqlengine import columns, management
from cassandra.cqlengine.models import Model
from cassandra.cqlengine.query import BatchQuery, DoesNotExist, LWTException
from memas.interface import corpus
from memas.interface.corpus import CorpusType
from memas.interface.exceptions import IllegalNameException, NamespaceDoesNotExistException, NamespaceExistsException
from memas.interface.namespace import ROOT_ID, ROOT_NAME, NAMESPACE_SEPARATOR, CORPUS_SEPARATOR, is_pathname_format_valid, is_name_format_valid
from memas.interface.storage_driver import MemasMetadataStore


_log = logging.getLogger(__name__)


MAX_PATH_LENGTH: Final[int] = 256
MAX_SEGMENT_LENGTH: Final[int] = 32
# -1 for "." separators
MAX_NS_NAME_LENGTH: Final[int] = MAX_SEGMENT_LENGTH - 1
# -1 for ":" separator
MAX_CORPUS_NAME_LENGTH: Final[int] = MAX_SEGMENT_LENGTH - 1


STD_READ_PERMISSION: Final[int] = 1
STD_WRITE_PERMISSION: Final[int] = 2
READ_AND_WRITE: Final[int] = STD_READ_PERMISSION & STD_WRITE_PERMISSION


class NamespaceNameToId(Model):
    """
    Maps full pathnames to ids, for both corpus and namespace.
    """
    # Full pathname, like `ns1.ns2.ns3` and `ns1.ns2:corpus`
    fullname = columns.Ascii(partition_key=True, max_length=MAX_PATH_LENGTH)
    id = columns.UUID(required=True)


class NamespaceParent(Model):
    """
    Maps child (both namespace and corpus) ids to parent ids within the namespace. 
    """
    child_id = columns.UUID(partition_key=True)
    parent_id = columns.UUID(required=True)


class NamespaceInfo(Model):
    """
    Table storing the Namespace's information
    """
    parent_id = columns.UUID(partition_key=True)
    namespace_id = columns.UUID(primary_key=True)

    parent_path = columns.Ascii(required=True, max_length=MAX_PATH_LENGTH - MAX_SEGMENT_LENGTH, min_length=0)
    namespace_name = columns.Ascii(required=True, max_length=MAX_NS_NAME_LENGTH)
    # Default set of (shared) corpora that is queried. This won't include the direct child corpora
    #   of this namespace, since those will always be queried unless specified otherwise.
    query_default_corpus = columns.Set(columns.UUID, default=set())
    created_at = columns.DateTime(required=True)


class CorpusInfo(Model):
    """
    Table storing the Corpus' information
    """
    parent_id = columns.UUID(partition_key=True)
    corpus_id = columns.UUID(primary_key=True)

    corpus_name = columns.Ascii(required=True, max_length=MAX_CORPUS_NAME_LENGTH)
    corpus_type = columns.Ascii(required=True)
    permissions = columns.Integer(required=True)
    created_at = columns.DateTime(required=True)


def split_namespace_pathname(pathname: str) -> tuple[str, str]:
    """Parses a namespace pathname into parent pathname and child name (NOT PATHNAME)

    Args:
        pathname (str): the full namespace pathname

    Returns:
        tuple[str, str]: (parent_pathname, namespace_name) pair
    """
    tokens = pathname.rsplit(NAMESPACE_SEPARATOR, 1)
    if len(tokens) == 1:
        return (ROOT_NAME, pathname)
    return (tokens[0], tokens[1])


def split_corpus_pathname(corpus_pathname: str) -> tuple[str, str]:
    """Parses a corpus pathname into parent pathname and child name (NOT PATHNAME)

    Args:
        pathname (str): the full corpus pathname

    Returns:
        tuple[str, str]: (parent_pathname, corpus_name) pair
    """
    tokens = corpus_pathname.split(CORPUS_SEPARATOR)
    if len(tokens) != 2:
        raise IllegalNameException(corpus_pathname)
    return (tokens[0], tokens[1])


class MemasMetadataStoreImpl(MemasMetadataStore):
    def init(self):
        management.sync_table(NamespaceNameToId)
        management.sync_table(NamespaceParent)
        management.sync_table(NamespaceInfo)
        management.sync_table(CorpusInfo)

    def first_init(self):
        self.init()

    def _get_id_by_name(self, fullname: str) -> uuid.UUID:
        # the root user currently only exists logically
        if fullname == ROOT_NAME:
            return ROOT_ID

        try:
            result = NamespaceNameToId.get(fullname=fullname)
        except DoesNotExist as e:
            raise NamespaceDoesNotExistException(fullname) from e
        return result.id

    def _get_ids_by_name(self, fullname: str) -> tuple[uuid.UUID, uuid.UUID]:
        if CORPUS_SEPARATOR in fullname:
            parent_pathname, child_name = split_corpus_pathname(fullname)
        else:
            parent_pathname, child_name = split_namespace_pathname(fullname)

        child_id = self._get_id_by_name(fullname=fullname)
        parent_id = self._get_id_by_name(fullname=parent_pathname)
        return (parent_id, child_id)

    def create_namespace(self, namespace_pathname: str, *, parent_id: uuid.UUID = None) -> uuid.UUID:
        _log.debug(f"Creating namespace for [namespace_pathname=\"{namespace_pathname}\"]")

        if namespace_pathname == ROOT_NAME:
            raise NamespaceExistsException(namespace_pathname, "\"\" is reserved for the root namespace!")
        if not is_pathname_format_valid(namespace_pathname):
            raise IllegalNameException(namespace_pathname)

        parent_pathname, child_name = split_namespace_pathname(namespace_pathname)
        if parent_id is None:
            parent_id = self._get_id_by_name(parent_pathname)

        namespace_id = uuid.uuid4()
        now = datetime.now()
        try:
            NamespaceNameToId.if_not_exists().create(fullname=namespace_pathname, id=namespace_id)
        except LWTException as e:
            _log.info(f"Namespace already exists [namespace_pathname=\"{namespace_pathname}\"]")
            raise NamespaceExistsException(namespace_pathname) from e

        # FIXME: Currently we don't handle the possibility of namespace ids colliding.
        #   On one hand this probability is extremely low; in our current state we don't expect
        #       a huge number of users
        #   On the other hand, this is costly to handle properly; if we were to separate this
        #       batch query into two queries, we increase the risk of interruptions
        with BatchQuery() as batch_query:
            NamespaceInfo.batch(batch_query).create(
                parent_id=parent_id, namespace_id=namespace_id,
                parent_path=parent_pathname, namespace_name=child_name, created_at=now)
            NamespaceParent.batch(batch_query).create(child_id=namespace_id, parent_id=parent_id)

        return namespace_id

    def create_corpus(self, corpus_pathname: str, corpus_type: CorpusType, permissions: int, *, parent_id: uuid.UUID = None) -> uuid.UUID:
        _log.debug(f"Creating corpus for [corpus_pathname=\"{corpus_pathname}\"] [corpus_type={corpus_type}]")

        parent_pathname, corpus_name = split_corpus_pathname(corpus_pathname)
        if not is_pathname_format_valid(parent_pathname) or not is_name_format_valid(corpus_name):
            raise IllegalNameException(corpus_pathname)

        if parent_id is None:
            parent_id = self._get_id_by_name(parent_pathname)

        corpus_id = uuid.uuid4()
        now = datetime.now()
        try:
            NamespaceNameToId.if_not_exists().create(fullname=corpus_pathname, id=corpus_id)
        except LWTException as e:
            _log.info(f"Corpus already exists [corpus_pathname=\"{corpus_pathname}\"]")
            raise NamespaceExistsException(corpus_pathname) from e

        # FIXME: Same issue with namespace id colliding.
        with BatchQuery() as batch_query:
            CorpusInfo.batch(batch_query).create(
                parent_id=parent_id, corpus_id=corpus_id, corpus_name=corpus_name,
                corpus_type=corpus_type.value, permissions=permissions, created_at=now)
            NamespaceParent.batch(batch_query).create(child_id=corpus_id, parent_id=parent_id)
        return corpus_id

    def create_conversation_corpus(self, corpus_pathname: str, *, parent_id: uuid.UUID = None) -> uuid.UUID:
        return self.create_corpus(corpus_pathname=corpus_pathname, corpus_type=CorpusType.CONVERSATION,
                                  permissions=READ_AND_WRITE, parent_id=parent_id)

    def create_knowledge_corpus(self, corpus_pathname: str, *, parent_id: uuid.UUID = None) -> uuid.UUID:
        return self.create_corpus(corpus_pathname=corpus_pathname, corpus_type=CorpusType.KNOWLEDGE,
                                  permissions=STD_READ_PERMISSION, parent_id=parent_id)

    def get_query_corpora(self, namespace_pathname: str) -> set[uuid.UUID]:
        parent_id, namespace_id = self._get_ids_by_name(namespace_pathname)
        namespace_result = NamespaceInfo.get(parent_id=parent_id, namespace_id=namespace_id)
        query_corpora = set(namespace_result.query_default_corpus)

        for corpora_result in CorpusInfo.filter(parent_id=namespace_id).all():
            query_corpora.add(corpora_result.corpus_id)
        return query_corpora

    def get_corpus_info(self, corpus_pathname: str) -> corpus.CorpusInfo:
        parent_id, corpus_id = self._get_ids_by_name(corpus_pathname)
        result = CorpusInfo.get(parent_id=parent_id, corpus_id=corpus_id)
        return corpus.CorpusInfo(corpus_pathname=corpus_pathname, corpus_id=corpus_id, corpus_type=CorpusType(result.corpus_type))


SINGLETON: MemasMetadataStore = MemasMetadataStoreImpl()
