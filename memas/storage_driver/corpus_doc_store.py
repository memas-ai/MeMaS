import logging
from typing import Final
from uuid import UUID
from elasticsearch import Elasticsearch, helpers
from memas.interface.storage_driver import CorpusDocumentStore, DocumentEntity


_log = logging.getLogger(__name__)


CORPUS_INDEX: Final[str] = "memas-documents"


CORPUS_FIELD: Final[str] = "corpus_id"
NAME_FIELD: Final[str] = "name"
DOC_FIELD: Final[str] = "content"


class ESDocumentStore(CorpusDocumentStore):
    def __init__(self, es: Elasticsearch) -> None:
        super().__init__()
        self.es: Elasticsearch = es
        self.es_index: str = CORPUS_INDEX

    def init(self):
        # nothing needed for ES
        return

    def first_init(self):
        mapping = {
            "properties": {
                CORPUS_FIELD: {
                    "type":  "keyword",
                    "index": True
                },
                NAME_FIELD: {
                    "type": "text",
                    "index": True
                },
                DOC_FIELD: {
                    "type":  "text",
                    "index": True
                },
            }
        }
        response = self.es.indices.create(
            index=self.es_index, mappings=mapping)
        return response["acknowledged"]

    def save_documents(self, id_doc_pairs: list[str, DocumentEntity]) -> bool:
        # TODO : Error handling in case of failures to insert
        # TODO : Redo this to have real return (this just checks that at least one insert succeeds)
        return helpers.bulk(self.es, self.gen_insertion_data(id_doc_pairs))[0] != 0

    def gen_insertion_data(self, id_doc_pairs: list[str, DocumentEntity]):
        _log.debug(
            f"Saving documents for [corpus_ids={[x[1].corpus_id for x in id_doc_pairs]}] [chunk_ids={[x[0] for x in id_doc_pairs]}]")
        for i in range(len(id_doc_pairs)):
            yield {
                "_index": self.es_index,
                "_id": id_doc_pairs[i][0],
                CORPUS_FIELD: id_doc_pairs[i][1].corpus_id.hex,
                NAME_FIELD: id_doc_pairs[i][1].document_name,
                DOC_FIELD: id_doc_pairs[i][1].document
            }

    def search_corpora(self, corpus_ids: list[UUID], clue: str) -> list[tuple[float, DocumentEntity]]:

        _log.debug(f"Searching documents for [corpus_ids={corpus_ids}]")

        # TODO: Need to look into how many documents to return
        max_retrieved = 20
        search_query = {
            "bool": {
                "must": [
                    {"match": {DOC_FIELD: clue}}
                ],
                "filter": [
                    {"terms":  {CORPUS_FIELD: [x.hex for x in corpus_ids]}}
                ]
            }
        }
        response = self.es.search(index=self.es_index, query=search_query, size=max_retrieved)

        # Record the time it took
        time = response["took"]
        _log.debug(f"Time it took for ES was {time}")

        result = []
        for hit in response["hits"]["hits"]:
            data = hit["_source"]
            result.append((hit["_score"], DocumentEntity(corpus_id=UUID(data[CORPUS_FIELD]), document_id=UUID(
                hit["_id"][:32]), document_name=data[NAME_FIELD], document=data[DOC_FIELD])))

        return result
