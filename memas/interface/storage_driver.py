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
        the namespace related data
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

    def get_corpus_info(self, corpus_pathname: str) -> CorpusInfo:
        """Gets the corpus info using the corpus pathname

        Args:
            corpus_pathname (str): the full pathname of the corpus

        Returns:
            CorpusInfo: Corpus Info object
        """

    def get_query_corpora(self, namespace_pathname: str) -> set[UUID]:
        """Retrieves the set of corpus ids this namespace user should query

        Args:
            namespace_pathname (str): the pathname of the querying user

        Returns:
            set[UUID]: set of corpus ids
        """


class CorpusDocumentMetadataStore(StorageDriver):
    """
        Metadata store for storing citations and other metadata for documents within the corpus.
    """
    @abstractmethod
    def insert_document_metadata(self, corpus_id: UUID, document_id: UUID, num_segments: int, document_name: str, citation: Citation) -> bool:
        """Inserts document metadata

        Args:
            corpus_id (UUID): corpus id
            document_id (UUID): document id
            document_name (str): document name
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


@dataclass
class DocumentEntity:
    corpus_id: UUID
    document_id: UUID
    document_name: str
    document: str


class CorpusDocumentStore(StorageDriver):
    """
        Corpus Document Store for storing and searching documents
    """
    @abstractmethod
    async def save_documents(self, chunk_id_doc_pairs: list[str, DocumentEntity]) -> bool:
        """Save a set of documents into the document store

        Args:
            id_doc_pairs (list[str, DocumentEntity]) : Pairs of documentIDs and Document Entities to insert

        Returns:
            bool: success or not
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
            doc_entities list[DocumentEntity]: List of Document Entity objects
        """
    @abstractmethod
    async def bulk_save_documents(self, doc_entities: list[DocumentEntity]) -> bool:
        """Saves a set of documents into the vector store using file transfer

        Args:
            doc_entities list[DocumentEntity]: List of Document Entity objects
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
