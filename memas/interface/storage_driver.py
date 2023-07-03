from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID
from interface.corpus import Citation


class StorageDriver(ABC):
    @abstractmethod
    def init(self):
        pass


class MemasMetadataStore(StorageDriver):
    @abstractmethod
    def create_conversation_corpus(self, parent_pathname: str, corpus_name: str) -> UUID:
        pass

    @abstractmethod
    def create_knowledge_corpus(self, parent_pathname: str, corpus_name: str) -> UUID:
        pass


class CorpusMetadataStore(StorageDriver):
    @abstractmethod
    def insert_document_metadata(self, corpus_id: UUID, document_id: UUID, document_name: str, citation: Citation):
        pass


@dataclass
class DocumentEntity:
    corpus_id: UUID
    document_id: UUID
    document_name: str
    document: str


class CorpusDocumentStore(StorageDriver):
    @abstractmethod
    def save_document(self, doc_entity: DocumentEntity) -> bool:
        pass

    @abstractmethod
    def search_corpus(self, corpus_id: UUID, clue: str) -> list[tuple[float, DocumentEntity]]:
        pass


class CorpusVectorStore(StorageDriver):
    pass
