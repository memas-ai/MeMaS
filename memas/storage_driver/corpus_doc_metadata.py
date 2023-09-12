from datetime import datetime
import logging
from uuid import UUID
from cassandra.cqlengine import columns, management
from cassandra.cqlengine.models import Model
from memas.interface.corpus import Citation
from memas.interface.storage_driver import CorpusDocumentMetadataStore


_log = logging.getLogger(__name__)


class DocumentMetadata(Model):
    corpus_id = columns.UUID(partition_key=True)
    document_id = columns.UUID(primary_key=True)

    document_name = columns.Text()
    source_name = columns.Text()
    source_uri = columns.Text()
    corpus_name = columns.Text()
    description = columns.Text()
    segment_count = columns.Integer()
    added_at = columns.DateTime(required=True)
    tags = columns.List(value_type=columns.Text)


class CorpusDocumentMetadataStoreImpl(CorpusDocumentMetadataStore):
    def init(self):
        management.sync_table(DocumentMetadata)

    def first_init(self):
        self.init()

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
        _log.debug(f"Inserting document metadata for [corpus_id={corpus_id.hex}] [document_id={document_id.hex}]")

        DocumentMetadata.create(corpus_id=corpus_id,
                                document_id=document_id,
                                document_name=document_name,
                                source_name=citation.source_name,
                                source_uri=citation.source_uri,
                                description=citation.description,
                                segment_count=num_segments,
                                added_at=datetime.now())
        return True

    def get_document_citation(self, corpus_id: UUID, document_id: UUID) -> Citation:
        """Retrieves the document citation

        Args:
            corpus_id (UUID): corpus id
            document_id (UUID): document id

        Returns:
            Citation: Citation object of the document
        """
        _log.debug(f"Retrieving document citation for [corpus_id={corpus_id.hex}] [document_id={document_id.hex}]")
        result = DocumentMetadata.get(
            corpus_id=corpus_id, document_id=document_id)
        return Citation(source_uri=result.source_uri,
                        source_name=result.source_name,
                        description=result.description)

    def get_document_segment_count(self, corpus_id: UUID, document_id: UUID) -> int:
        """Retrieves the number of segments a stored document was split into 

        Args:
            corpus_id (UUID): corpus id
            document_id (UUID): document id

        Returns:
            int: the number of segments the document is broken into
        """
        _log.debug(f"Retrieving document segment count for [corpus_id={corpus_id.hex}] [document_id={document_id.hex}]")
        return DocumentMetadata.get(corpus_id=corpus_id, document_id=document_id).segment_count


SINGLETON: CorpusDocumentMetadataStore = CorpusDocumentMetadataStoreImpl()
