import pytest
from unittest import mock
from cassandra.cqlengine.query import DoesNotExist

from memas.interface.exceptions import NamespaceDoesNotExistException
from memas.interface.namespace import ROOT_ID
from memas.storage_driver.memas_metadata import split_corpus_pathname, split_namespace_pathname
from memas.storage_driver.memas_metadata import MemasMetadataStoreImpl


def test_split_corpus_pathname():
    assert split_corpus_pathname("namespace.user:memory") == ("namespace.user", "memory")


def test_split_namespace_pathname():
    assert split_namespace_pathname("namespace.user.bot") == ("namespace.user", "bot")


def test_get_id_by_name_root():
    store = MemasMetadataStoreImpl()
    assert ROOT_ID == store._get_id_by_name("")


@mock.patch('memas.storage_driver.memas_metadata.NamespaceNameToId')
def test_get_id_by_name_doesnt_exist(name_to_id):
    name_to_id.get.side_effect = DoesNotExist()

    store = MemasMetadataStoreImpl()
    with pytest.raises(NamespaceDoesNotExistException):
        store._get_id_by_name("XD")
