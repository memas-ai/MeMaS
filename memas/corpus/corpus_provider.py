import logging
from uuid import UUID
from memas.corpus.basic_corpus import BasicCorpusFactory
from memas.interface.corpus import Corpus, CorpusFactory, CorpusType
from memas.interface.storage_driver import CorpusDocumentMetadataStore, CorpusDocumentStore, CorpusVectorStore


_log = logging.getLogger(__name__)


class CorpusProvider:
    def __init__(self, metadata_store: CorpusDocumentMetadataStore, doc_store: CorpusDocumentStore, vec_store: CorpusVectorStore) -> None:
        self.factory_dict: dict[CorpusType, CorpusFactory] = dict()

        basic_corpus_factory = BasicCorpusFactory(metadata_store, doc_store, vec_store)
        self.factory_dict[CorpusType.CONVERSATION] = basic_corpus_factory
        self.factory_dict[CorpusType.KNOWLEDGE] = basic_corpus_factory

    def get_corpus(self, corpus_id: UUID, *, corpus_type: CorpusType, namespace_id: UUID = None) -> Corpus:
        """Gets the Corpus class based on the corpus_id

        Args:
            corpus_id (UUID): corpus_id
            corpus_type (CorpusType): type of the corpus, this is necessary unless a namespace_id is provided
            namespace_id (UUID): namespace_id of the corpus, this is necessary when a corpus type is not provided, 
                since it's needed to find the corpus type.

        Returns:
            Corpus: _description_
        """
        return self.factory_dict[corpus_type].produce(corpus_id)
