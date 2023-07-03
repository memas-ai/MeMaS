from typing import Final
from uuid import UUID
from memas.interface.storage_driver import CorpusDocumentStore, DocumentEntity
from elasticsearch import Elasticsearch


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

    def save_document(self, doc_entity: DocumentEntity) -> bool:
        doc = {
            CORPUS_FIELD: doc_entity.corpus_id.hex,
            NAME_FIELD: doc_entity.document_name,
            DOC_FIELD: doc_entity.document
        }
        response = self.es.create(
            index=self.es_index, id=doc_entity.document_id.hex, document=doc)
        return response['result'] == 'created'

    def search_corpus(self, corpus_id: UUID, clue: str) -> list[tuple[float, DocumentEntity]]:
        search_query = {
            "bool": {
                "must": [
                    {"match": {DOC_FIELD: clue}}
                ],
                "filter": [
                    {"term":  {CORPUS_FIELD: corpus_id.hex}}
                ]
            }
        }
        response = self.es.search(index=self.es_index, query=search_query)

        result = []
        for hit in response["hits"]["hits"]:
            data = hit["_source"]
            result.append((hit["_score"], DocumentEntity(corpus_id=UUID(data[CORPUS_FIELD]), document_id=UUID(
                hit["_id"]), document_name=data[NAME_FIELD], document=data[DOC_FIELD])))

        return result
