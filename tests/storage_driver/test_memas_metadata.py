
from memas.storage_driver.memas_metadata import split_corpus_pathname, split_namespace_pathname


def test_split_corpus_pathname():
    assert split_corpus_pathname("namespace.user:memory") == ("namespace.user", "memory")


def test_split_namespace_pathname():
    assert split_namespace_pathname("namespace.user.bot") == ("namespace.user", "bot")
