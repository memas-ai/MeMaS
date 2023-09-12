# from search_redirect import SearchSettings
import logging
import uuid
from functools import reduce
from memas.interface.corpus import Corpus, CorpusFactory
from memas.interface.corpus import Citation
from memas.interface.storage_driver import DocumentEntity
from memas.interface.exceptions import SentenceLengthOverflowException
from memas.context_manager import ctx
from memas.text_parsing.text_parsers import segment_document
from memas.corpus.corpus_searching import normalize_and_combine
import asyncio

import platform

MAX_SEGMENT_LENGTH = 1536

_log = logging.getLogger(__name__)


class BasicCorpus(Corpus):

    def __init__(self, corpus_id: uuid.UUID, corpus_name: str):
        super().__init__(corpus_id, corpus_name)

    """
    The function stores a document in the elastic search DB, vecDB, and doc MetaData.
    Returns True on Success, False on Failure
    """

    async def store_and_index(self, doc_name_text_cit_triples : list[tuple[str, str, Citation]]) -> bool:

        if platform.system()=='Windows':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        # _log.debug(f"Corpus storing and indexing [corpus_id={self.corpus_id}] with data={doc_name_text_cit_triples}")
        doc_entities_to_save : list[DocumentEntity] = []
        chunk_id_entity_pairs = []
        meta_save = True

        for doc_obj in doc_name_text_cit_triples :
            document_name = doc_obj[0]
            document = doc_obj[1]
            citation = doc_obj[2]

            doc_id = uuid.uuid4()
            doc_entity = DocumentEntity(corpus_id=self.corpus_id, document_id=doc_id, document_name=document_name, document=document)

            document_chunks = segment_document(document, MAX_SEGMENT_LENGTH)

            # TODO : Need to investigate how to undo when failures on partial insert
            last_save = ctx.corpus_metadata.insert_document_metadata(
                            self.corpus_id, doc_id, len(document_chunks), document_name, citation)
            
            meta_save = meta_save and last_save

            doc_entities_to_save.append(doc_entity)

            # Divide longer documents for document store
            chunk_num = 0
            for chunk in document_chunks:
                # Create the new IDs for the document chunk combo
                chunk_id = doc_id.hex + '{:032b}'.format(chunk_num)
                chunk_num = chunk_num + 1
                doc_chunk_entity = DocumentEntity(self.corpus_id, doc_id, document_name, chunk)
                chunk_id_entity_pairs.append((chunk_id, doc_chunk_entity))

        # Insert all chunks and vectors of documents at once
        doc_save = ctx.corpus_doc.save_documents(id_doc_pairs=chunk_id_entity_pairs)
        # TODO: decide when to bulk insert vs not
        vec_save = ctx.corpus_vec.bulk_save_documents(doc_entities_to_save)
        #vec_save2 = ctx.corpus_vec.save_documents(doc_entities_to_save)
        # await doc_save
        #await vec_save
        await asyncio.gather(doc_save, vec_save)
        # await asyncio.gather(ctx.corpus_doc.save_documents(id_doc_pairs=chunk_id_entity_pairs))#, ctx.corpus_vec.save_documents(doc_entities_to_save))

        # _log.debug(f"Save sucess per DB is : [docDB={doc_save}, metaDB={meta_save}, vecDB={vec_save}]")
        # return meta_save #and vec_save and doc_save

    """
    The most basic search of a document store via Elastic Search and a Vector DB
    via ANN. Combines the result via a simple concatenation.
    """

    def search(self, clue: str) -> list[tuple[str, Citation]]:
        _log.debug(f"Corpus searching [corpus_id={self.corpus_id}]")

        doc_store_results: list[tuple[float, str, Citation]] = []
        temp_res = ctx.corpus_doc.search_corpora([self.corpus_id], clue)
        # Search the document store
        for score, doc_entity in temp_res:
            document_text = doc_entity.document
            citation = ctx.corpus_metadata.get_document_citation(self.corpus_id, doc_entity.document_id)
            doc_store_results.append([score, document_text, citation])

        # Search for the vectors
        vec_store_results: list[tuple[float, str, Citation]] = []
        temp_res2 = ctx.corpus_vec.search_corpora([self.corpus_id], clue)
        _log.debug(f"COrpus search Vec results are ={temp_res2}]")
        for score, doc_entity, start_index, end_index in temp_res2:

            # Verify that the text recovered from the vectors fits the maximum sentence criteria
            if end_index - start_index != len(doc_entity.document):
                _log.error("Index not aligned with actual document", exc_info=True)
                raise SentenceLengthOverflowException(end_index - start_index)

            citation = ctx.corpus_metadata.get_document_citation(self.corpus_id, doc_entity.document_id)
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

    def generate_search_instructions(self, clue: str) -> any:
        pass


class BasicCorpusFactory(CorpusFactory):
    def produce(self, corpus_id: uuid.UUID):
        # TODO: Maybe change the Corpus Name Parameter
        return BasicCorpus(corpus_id, "BasicCorpus")
