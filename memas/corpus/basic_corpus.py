# from search_redirect import SearchSettings
import logging
import uuid
from memas.interface.corpus import Corpus, CorpusFactory
from memas.interface.corpus import Citation
from memas.interface.storage_driver import CorpusDocumentMetadataStore, CorpusDocumentStore, CorpusVectorStore, DocumentEntity
from memas.interface.exceptions import SentenceLengthOverflowException
from memas.text_parsing.text_parsers import segment_document
from memas.corpus.corpus_searching import normalize_and_combine

MAX_SEGMENT_LENGTH = 1536

_log = logging.getLogger(__name__)


class BasicCorpus(Corpus):

    def __init__(self, corpus_id: uuid.UUID, corpus_name: str, metadata_store: CorpusDocumentMetadataStore, doc_store: CorpusDocumentStore, vec_store: CorpusVectorStore):
        super().__init__(corpus_id, corpus_name)
        self.metadata_store: CorpusDocumentMetadataStore = metadata_store
        self.doc_store: CorpusDocumentStore = doc_store
        self.vec_store: CorpusVectorStore = vec_store

    """
    The function stores a document in the elastic search DB, vecDB, and doc MetaData.
    Returns True on Success, False on Failure
    """

    def store_and_index(self, document: str, citation: Citation) -> bool:
        _log.debug(f"Corpus storing and indexing [corpus_id={self.corpus_id}]")

        doc_id = uuid.uuid4()
        doc_entity = DocumentEntity(self.corpus_id, doc_id, citation.document_name, document)

        document_chunks = segment_document(document, MAX_SEGMENT_LENGTH)

        # TODO : Need to investigate how to undo when failures on partial insert
        meta_save = self.metadata_store.insert_document_metadata(
            self.corpus_id, doc_id, len(document_chunks), citation)

        vec_save = self.vec_store.save_documents([doc_entity])

        # Divide longer documents for document store
        chunk_num = 0
        chunk_id_entity_pairs = []
        for chunk in document_chunks:
            # Create the new IDs for the document chunk combo
            chunk_id = doc_id.hex + '{:032b}'.format(chunk_num)
            chunk_num = chunk_num + 1
            doc_chunk_entity = DocumentEntity(self.corpus_id, doc_id, citation.document_name, chunk)
            chunk_id_entity_pairs.append((chunk_id, doc_chunk_entity))

        # Insert all chunks of document at once
        doc_save = self.doc_store.save_documents(id_doc_pairs=chunk_id_entity_pairs)

        return meta_save and vec_save and doc_save

    """
    The most basic search of a document store via Elastic Search and a Vector DB
    via ANN. Combines the result via a simple concatenation.
    """

    def search(self, clue: str) -> list[tuple[float, str, Citation]]:
        _log.debug(f"Corpus searching [corpus_id={self.corpus_id}]")

        # TODO : Replace the fields that constrain and describe the search with a SearchSettings Object
        # that can be passed in
        vector_search_count: int = 10

        doc_store_results: list[tuple[float, str, Citation]] = []
        temp_res = self.doc_store.search_corpora([self.corpus_id], clue)
        # Search the document store
        for score, doc_entity in temp_res:
            document_text = doc_entity.document
            citation = self.metadata_store.get_document_citation(self.corpus_id, doc_entity.document_id)
            doc_store_results.append([score, document_text, citation])

        # Search for the vectors
        vec_store_results: list[tuple[float, str, Citation]] = []
        temp_res2 = self.vec_store.search_corpora([self.corpus_id], clue)
        for score, doc_entity, start_index, end_index in temp_res2:

            # Verify that the text recovered from the vectors fits the maximum sentence criteria
            if end_index - start_index != len(doc_entity.document):
                _log.error("Index not aligned with actual document", exc_info=True)
                raise SentenceLengthOverflowException(end_index - start_index)

            citation = self.metadata_store.get_document_citation(self.corpus_id, doc_entity.document_id)
            vec_store_results.append([score, doc_entity.document, citation])

        # If any of the searches returned no results combine and return
        if len(vec_store_results) == 0:
            doc_store_results.sort(key=lambda x: x[0], reverse=True)
            results = [(y, z) for [x, y, z] in doc_store_results]
        elif len(doc_store_results) == 0:
            vec_store_results.sort(key=lambda x: x[0], reverse=False)
            results = [(y, z) for [x, y, z] in vec_store_results]
        else:
            # Combine the results and remove duplicates
            results = normalize_and_combine(doc_store_results, vec_store_results)

        return results


class BasicCorpusFactory(CorpusFactory):
    def __init__(self, metadata_store: CorpusDocumentMetadataStore, doc_store: CorpusDocumentStore, vec_store: CorpusVectorStore) -> None:
        super().__init__()
        self.metadata_store: CorpusDocumentMetadataStore = metadata_store
        self.doc_store: CorpusDocumentStore = doc_store
        self.vec_store: CorpusVectorStore = vec_store
    
    def produce(self, corpus_id: uuid.UUID):
        # TODO: Maybe change the Corpus Name Parameter
        return BasicCorpus(corpus_id, "BasicCorpus", self.metadata_store, self.doc_store, self.vec_store)
