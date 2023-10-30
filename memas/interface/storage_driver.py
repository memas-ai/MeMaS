from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID
from memas.interface.corpus import Citation, CorpusInfo
from memas.interface.encoder import TextEncoder


class StorageDriver(ABC):
    """
        Storage driver abstract base class
    """
    @abstractmethod
    def init(self):
        """Initialize the storage driver. This is ran every time on server startup
        """

    @abstractmethod
    def first_init(self):
        """First time initiliaze the storage driver. This is mostly for operations that you only 
        want to run once, like create table
        """


class MemasMetadataStore(StorageDriver):
    """
        Memas metadata store providing basic namespace level operations for managing 
        the namespace related metadata
    """

    @abstractmethod
    def get_namespace_ids_by_name(self, fullname: str) -> tuple[UUID, UUID]:
        """Retrieve the parent and child namespace_id from the pathname

        Args:
            fullname (str): the full pathname

        Returns:
            tuple[UUID, UUID]: (parent_id, child_id) pair
        """

    @abstractmethod
    def get_corpus_ids_by_name(self, fullname: str) -> tuple[UUID, UUID]:
        """Retrieve the parent namespace_id and the child corpus id from the pathname

        Args:
            fullname (str): the full pathname

        Returns:
            tuple[UUID, UUID]: (parent_id, child_id) pair
        """

    @abstractmethod
    def create_namespace(self, namespace_pathname: str, *, parent_id: UUID = None) -> UUID:
        """Create a namespace based on the pathname

        Args:
            namespace_pathname (str): pathname of the namespace to be created
            parent_id (UUID, optional): UUID of the parent namespace. This will be 
                retrieved based on pathname if not supplied.

        Returns:
            UUID: uuid of the just created namespace
        """

    @abstractmethod
    def create_conversation_corpus(self, corpus_pathname: str, *, parent_id: UUID = None) -> UUID:
        """Create a conversation corpus based on the pathname

        Args:
            corpus_pathname (str): pathname of the namespace to be created
            parent_id (UUID, optional): UUID of the parent namespace. This will be 
                retrieved based on pathname if not supplied.

        Returns:
            UUID: uuid of the just created corpus
        """

    @abstractmethod
    def create_knowledge_corpus(self, corpus_pathname: str, *, parent_id: UUID = None) -> UUID:
        """Create a knowledge corpus based on the pathname

        Args:
            corpus_pathname (str): pathname of the namespace to be created
            parent_id (UUID, optional): UUID of the parent namespace. This will be 
                retrieved based on pathname if not supplied.

        Returns:
            UUID: uuid of the just created corpus
        """

    @abstractmethod
    def get_corpus_info(self, corpus_pathname: str) -> CorpusInfo:
        """Gets the corpus info using the corpus pathname

        Args:
            corpus_pathname (str): the full pathname of the corpus

        Returns:
            CorpusInfo: Corpus Info object
        """

    @abstractmethod
    def get_corpus_info_by_id(self, namespace_id: UUID, corpus_id: UUID) -> CorpusInfo:
        """Gets the corpus info using the corpus id and namespace id

        Args:
            namespace_id (UUID): parent namespace id of the corpus
            corpus_id (UUID): corpus id of the corpus

        Returns:
            CorpusInfo: Corpus Info object
        """

    @abstractmethod
    def get_query_corpora(self, namespace_pathname: str) -> set[CorpusInfo]:
        """Retrieves the set of CorpusInfo objects this namespace user should query

        Args:
            namespace_pathname (str): the pathname of the querying user

        Returns:
            set[CorpusInfo]: set of CorpusInfo objects
        """

    @abstractmethod
    def initiate_delete_corpus(self, parent_id: UUID, corpus_id: UUID, corpus_pathname: str):
        """Initiate corpus deletion. This will free up the pathname, while marking the corpus as deleted.
        Note that the parent and corpus ids are needed when recovering an interrupted delete

        Args:
            parent_id (UUID): parent namespace id of the corpus
            corpus_id (UUID): child corpus id of the corpus
            corpus_pathname (str): the full pathname of the corpus
        """

    @abstractmethod
    def finish_delete_corpus(self, parent_id: UUID, corpus_id: UUID):
        """Finish corpus deletion. This will fully delete a corpus' metadata.

        Args:
            parent_id (UUID): parent namespace id of the corpus
            corpus_id (UUID): corpus id of the corpus
        """


class CorpusDocumentMetadataStore(StorageDriver):
    """
        Metadata store for storing citations and other metadata for documents within the corpus.
    """
    @abstractmethod
    def insert_document_metadata(self, corpus_id: UUID, document_id: UUID, num_segments: int, citation: Citation) -> bool:
        """Inserts document metadata

        Args:
            corpus_id (UUID): corpus id
            document_id (UUID): document id
            num_segments (int): number of segments the document is stored in
            citation (Citation): citation object

        Returns:
            bool: success or not
        """

    @abstractmethod
    def get_document_citation(self, corpus_id: UUID, document_id: UUID) -> Citation:
        """Retrieves the document citation

        Args:
            corpus_id (UUID): corpus id
            document_id (UUID): document id

        Returns:
            Citation: Citation object of the document
        """

    @abstractmethod
    def delete_corpus(self, corpus_id: UUID):
        """Deletes all citations under a corpus

        Args:
            corpus_id (UUID): corpus id
        """


@dataclass
class DocumentEntity:
    corpus_id: UUID
    document_id: UUID
    # while strictly speaking this is metadata, this increases data readability
    document_name: str
    document: str


class CorpusDocumentStore(StorageDriver):
    """
        Corpus Document Store for storing and searching documents
    """
    @abstractmethod
    def save_documents(self, id_doc_pairs: list[str, DocumentEntity]) -> bool:
        """Save a set of documents into the document store

        Args:
            id_doc_pairs (list[str, DocumentEntity]) : Pairs of documentIDs and Document Entities to insert

        Returns:
            bool: success or not
        """

    @abstractmethod
    def delete_corpus(self, corpus_id: UUID):
        """delete all documents under a corpus

        Args:
            corpus_id (UUID): corpus id
        """

    @abstractmethod
    def search_corpora(self, corpus_ids: list[UUID], clue: str) -> list[tuple[float, DocumentEntity]]:
        """Search set of corpora using a clue

        Args:
            corpus_ids list[UUID]: corpus ids
            clue (str): clue to search with

        Returns:
            list[tuple[float, DocumentEntity]]: list of (score,document) pairs
        """


class CorpusVectorStore(StorageDriver):
    """
        Corpus Vector Store for storing and searching with vectors
    """

    def __init__(self, encoder: TextEncoder) -> None:
        super().__init__()
        self.encoder: TextEncoder = encoder

    @abstractmethod
    def save_documents(self, doc_entities: list[DocumentEntity]) -> bool:
        """Saves a document into the vector store

        Args:
            doc_entity (DocumentEntity): Document Entity object
        """

    @abstractmethod
    def delete_corpus(self, corpus_id: UUID):
        """delete all vectors under a corpus

        Args:
            corpus_id (UUID): the corpus id
        """

    @abstractmethod
    def search_corpora(self, corpus_ids: list[UUID], clue: str) -> list[tuple[float, DocumentEntity, int, int]]:
        """Search set of corpora using a clue

        Args:
            corpus_ids list[UUID]: corpus ids
            clue (str): clue to search with

        Returns:
            list[tuple[float, DocumentEntity]]: list of (score, document. startIndex, endIndex) pairs that deonte sentence boundaries
        """
