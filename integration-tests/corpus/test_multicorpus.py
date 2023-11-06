import numpy as np
import uuid
import time
from memas.corpus import basic_corpus
from memas.corpus.corpus_searching import multi_corpus_search
from memas.interface.corpus import Citation, CorpusInfo, CorpusType

corpus_name = "test corpus1"


def test_multicorpus_search(ctx, test_client):
    namespace_id = uuid.uuid4()
    corpus_id1 = uuid.uuid4()
    corpus_id2 = uuid.uuid4()
    corpus_id3 = uuid.uuid4()
    corpus_info1 = CorpusInfo("test_corpus1", namespace_id, corpus_id1, CorpusType.CONVERSATION)
    corpus_info2 = CorpusInfo("test_corpus2", namespace_id, corpus_id2, CorpusType.KNOWLEDGE)
    corpus_info3 = CorpusInfo("test_corpus3", namespace_id, corpus_id3, CorpusType.CONVERSATION)
    test_corpus1 = basic_corpus.BasicCorpus(corpus_info1, ctx.corpus_metadata, ctx.corpus_doc, ctx.corpus_vec)
    test_corpus2 = basic_corpus.BasicCorpus(corpus_info2, ctx.corpus_metadata, ctx.corpus_doc, ctx.corpus_vec)
    test_corpus3 = basic_corpus.BasicCorpus(corpus_info3, ctx.corpus_metadata, ctx.corpus_doc, ctx.corpus_vec)

    text1 = "The sun is high. California sunshine is great. "
    text2 = "I picked up my phone and then dropped it again. I cant seem to get a good grip on things these days. It persists into my everyday tasks"
    text3 = "The weather is great today, but I worry that tomorrow it won't be. My umbrella is in the repair shop."

    assert test_corpus1.store_and_index(text1, Citation("www.docsource1", "SSSdoc1", "", "doc1"))
    assert test_corpus2.store_and_index(text2, Citation("were.docsource2", "SSSdoc2", "", "doc2"))
    assert test_corpus3.store_and_index(text3, Citation("docsource3.ai", "SSSdoc3", "", "doc3"))

    time.sleep(1)

    corpus_dict = {}
    corpus_dict[CorpusType.CONVERSATION] = [test_corpus1, test_corpus3]
    corpus_dict[CorpusType.KNOWLEDGE] = [test_corpus2]

    output = multi_corpus_search(corpus_dict, "It is sunny", ctx, 5)
    # Check that text was retrieved from all 3 corpuses upon searching
    assert len(output) == 3

    assert "sunshine" in output[1][1]
    assert "weather" in output[0][1]
