from typing import Final
from enum import Enum
from cassandra.cqlengine import columns, management
from cassandra.cqlengine.models import Model


class MemoryMetadata(Model):
    corpus_id = columns.UUID(partition_key=True)
    document_id = columns.UUID(primary_key=True)

    document_name = columns.Text(required=True)
    corpus_fullname = columns.Text(required=True)
    source_name = columns.Text(required=True)
    source_uri = columns.Text()
    description = columns.Text()
    added_at = columns.Time(required=True)
    tags = columns.List(value_type=columns.Text)


# class DocumentIdToName(Model):
#     document_id         = columns.UUID(partition_key=True)
#     document_name       = columns.Text(required=True)
#     corpus_fullname     = columns.Text(required=True)


def init():
    management.sync_table(MemoryMetadata)
    # management.sync_table(DocumentIdToName)
