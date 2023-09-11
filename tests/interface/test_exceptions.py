import pytest
from memas.interface.exceptions import ErrorCode, MemasException


def test_memas_exception_output_object():
    e = MemasException(ErrorCode.NamespaceExists, "test message", additional_details="test details")

    assert e.return_obj() == {"error_code": ErrorCode.NamespaceExists.value,
                              "msg": "test message", "details": "test details"}


def test_memas_exception_details():
    e = MemasException(ErrorCode.NamespaceExists, "test message")

    assert "details" not in e.return_obj()
