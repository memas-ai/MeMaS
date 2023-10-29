import pytest
from memas.interface.namespace import is_namespace_pathname_valid, is_corpus_pathname_valid, is_name_format_valid, mangle_corpus_pathname


@pytest.mark.parametrize("parent_pathname, corpus_name, expected_pathname", [
    ("aaa.bbb", "ccc", "aaa.bbb:ccc"),
])
def test_mangle_corpus_pathname(parent_pathname, corpus_name, expected_pathname):
    assert mangle_corpus_pathname(parent_pathname, corpus_name) == expected_pathname


@pytest.mark.parametrize("pathname", [
    "aaa.bbb.ccc",  # most standard namespace
    "",  # The empty string namespace is the reserved root namespace
    "c",  # Single character names are allowed
    "AFD.my.namespace"  # capital case is allowed
])
def test_namespace_pathname_format_valid(pathname):
    assert is_namespace_pathname_valid(pathname)


@pytest.mark.parametrize("pathname", [
    "a.bb:ccc",  # most standard corpus
    ":corpus",  # root level corpus
])
def test_corpus_pathname_format_valid(pathname):
    assert is_corpus_pathname_valid(pathname)


@pytest.mark.parametrize("pathname", [
    "x y",  # No spaces allowed
    "this,is\"also;bad",  # no weird separators
    "a..b",  # only the root namespace can be empty
    "a.bb:ccc",  # most standard corpus
    ":corpus",  # root level corpus
])
def test_namespace_pathname_format_invalid(pathname):
    assert not is_namespace_pathname_valid(pathname)


@pytest.mark.parametrize("pathname", [
    "x y",  # No spaces allowed
    "this,is\"also;bad",  # no weird separators
    "a..b",  # only the root namespace can be empty
    "aaa.bbb.ccc",  # most standard namespace
    "",  # The empty string namespace is the reserved root namespace
    "c",  # Single character names are allowed
    "AFD.my.namespace"  # capital case is allowed
])
def test_corpus_pathname_format_invalid(pathname):
    assert not is_corpus_pathname_valid(pathname)


@pytest.mark.parametrize("name", [
    "abc",
    "x",
    "aBc",
    "MeMaS",
    "xyz99",
    "12345",
    "a" * 31,
    "max_yu",  # the _ is one of the few allowed non-character symbols
])
def test_name_format_valid(name):
    assert is_name_format_valid(name)


@pytest.mark.parametrize("name", [
    "",  # Empty string names are not allowed
    ".x",  # separators are not allowed
    ":x",
    "a-b",  # the - is currently reserved as well
    "记忆",  # utf characters are currently not allowed
    "my name",  # Currently don't allow whitespace characters as well
])
def test_name_format_invalid(name):
    assert not is_name_format_valid(name)
