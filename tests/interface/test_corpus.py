import uuid
from memas.interface.corpus import CorpusInfo, CorpusType


def test_corpus_info_hashable():
    namespace_id1 = uuid.uuid4()
    corpus_id1 = uuid.uuid4()
    corpus_info1 = CorpusInfo("test1", namespace_id1, corpus_id1, CorpusType.CONVERSATION)

    try:
        s = {corpus_info1}
    except TypeError:
        assert False, "CorpusInfo is not hashable"
