from uuid import UUID
from memas.interface.corpus import Corpus, CorpusFactory, CorpusType


class CorpusProvider:
    def __init__(self) -> None:
        self.factory_dict: dict[CorpusType, CorpusFactory] = dict()

    def get_corpus(self, corpus_id: UUID, *, corpus_type: CorpusType, namespace_id: UUID) -> Corpus:
        """Gets the Corpus class based on the corpus_id

        Args:
            corpus_id (UUID): corpus_id
            corpus_type (CorpusType): type of the corpus, this is necessary unless a namespace_id is provided
            namespace_id (UUID): namespace_id of the corpus. This is necessary when

        Returns:
            Corpus: _description_
        """
        return self.factory_dict[corpus_type].produce(corpus_id)
