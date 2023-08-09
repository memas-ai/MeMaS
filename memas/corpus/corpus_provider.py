from uuid import UUID
from memas.interface.corpus import Corpus, CorpusFactory, CorpusType


class CorpusProvider:
    def __init__(self) -> None:
        self.factory_dict: dict[CorpusType, CorpusFactory] = dict()

    def setCorpusFactory(self, corpus_type: CorpusType, corpus_factory: CorpusFactory):
        self.factory_dict[corpus_type] = corpus_factory

    # TODO : Fix the last parameter that was just removed - what is that supposed to be for? namespace_id

    def get_corpus(self, corpus_id: UUID, *, corpus_type: CorpusType) -> Corpus:
        """Gets the Corpus class based on the corpus_id

        Args:
            corpus_id (UUID): corpus_id
            corpus_type (CorpusType): type of the corpus, this is necessary unless a namespace_id is provided
            namespace_id (UUID): namespace_id of the corpus. This is necessary when

        Returns:
            Corpus: _description_
        """
        return self.factory_dict[corpus_type].produce(corpus_id)
