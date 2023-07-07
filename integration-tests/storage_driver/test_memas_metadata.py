import pytest
from memas.interface.exceptions import NamespaceExistsException
from memas.interface.namespace import ROOT_ID
from memas.storage_driver.memas_metadata import MemasMetadataStoreImpl


def test_init(cassandra_client):
    metadata = MemasMetadataStoreImpl()
    metadata.init()


def test_create_namespace(cassandra_client):
    metadata = MemasMetadataStoreImpl()
    metadata.init()

    namespace_id = metadata.create_namespace("integ_test", parent_id=ROOT_ID)
    assert metadata._get_id_by_name("integ_test") == namespace_id

    with pytest.raises(NamespaceExistsException):
        namespace_id = metadata.create_namespace("integ_test", parent_id=ROOT_ID)
