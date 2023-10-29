import logging
from memas.corpus.basic_corpus import BasicCorpusFactory
from memas.interface.corpus import Corpus, CorpusFactory, CorpusInfo, CorpusType
from memas.interface.storage_driver import CorpusDocumentMetadataStore, CorpusDocumentStore, CorpusVectorStore, MemasMetadataStore


_log = logging.getLogger(__name__)


class CorpusProvider:
    def __init__(self,
                 memas_metadata_store: MemasMetadataStore,
                 doc_metadata_store: CorpusDocumentMetadataStore,
                 doc_store: CorpusDocumentStore,
                 vec_store: CorpusVectorStore
                 ) -> None:
        self.memas_metadata_store: MemasMetadataStore = memas_metadata_store

        self.factory_dict: dict[CorpusType, CorpusFactory] = dict()

        basic_corpus_factory = BasicCorpusFactory(doc_metadata_store, doc_store, vec_store)
        self.factory_dict[CorpusType.CONVERSATION] = basic_corpus_factory
        self.factory_dict[CorpusType.KNOWLEDGE] = basic_corpus_factory

    def get_corpus_by_name(self, corpus_pathname: str) -> Corpus:
        """Gets the Corpus class based on the corpus_pathname

        Args:
            corpus_pathname (str): corpus pathname

        Returns:
            Corpus: Corpus object for searching
        """
        corpus_info = self.memas_metadata_store.get_corpus_info(corpus_pathname)
        return self.get_corpus_by_info(corpus_info)

    def get_corpus_by_info(self, corpus_info: CorpusInfo) -> Corpus:
        """Gets the Corpus class based on the CorpusInfo

        Args:
            corpus_info (CorpusInfo): corpus info object

        Returns:
            Corpus: Corpus object for searching
        """
        return self.factory_dict[corpus_info.corpus_type].produce(corpus_info)
