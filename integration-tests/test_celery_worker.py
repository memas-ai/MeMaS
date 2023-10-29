import pytest
from unittest import mock
import memas.celery_worker
from memas.interface.exceptions import NamespaceDoesNotExistException


@mock.patch("memas.celery_worker.time.sleep")
def test_delete_corpus(mock_sleep, ctx):
    namespace_id = ctx.memas_metadata.create_namespace("celery_delete_corpus")
    corpus_pathname = "celery_delete_corpus:corpus1"
    corpus_id = ctx.memas_metadata.create_conversation_corpus(corpus_pathname)
    memas.celery_worker.delete_corpus(namespace_id, corpus_id, corpus_pathname)

    with pytest.raises(NamespaceDoesNotExistException):
        ctx.memas_metadata.get_corpus_ids_by_name(corpus_pathname)
