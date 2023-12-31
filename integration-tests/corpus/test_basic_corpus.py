import numpy as np
import uuid
import time
from memas.corpus import basic_corpus
from memas.interface.corpus import Citation, CorpusInfo, CorpusType

corpus_name = "test corpus1"


def test_save_then_search_one_corpus(ctx):
    namespace_id = uuid.uuid4()
    corpus_id = uuid.uuid4()
    corpus_info = CorpusInfo("test_corpus_save_search", namespace_id, corpus_id, CorpusType.CONVERSATION)
    test_corpus = basic_corpus.BasicCorpus(corpus_info, ctx.corpus_metadata, ctx.corpus_doc, ctx.corpus_vec)

    text1 = "The sun is high. California sunshine is great. "
    text2 = "I picked up my phone and then dropped it again. I cant seem to get a good grip on things these days. It persists into my everyday tasks"
    text3 = "The weather is great today, but I worry that tomorrow it won't be. My umbrella is in the repair shop."

    assert test_corpus.store_and_index(text1, Citation("www.docsource1", "SSSdoc1", "", "doc1"))
    assert test_corpus.store_and_index(text2, Citation("were.docsource2", "SSSdoc2", "", "doc2"))
    assert test_corpus.store_and_index(text3, Citation("docsource3.ai", "SSSdoc3", "", "doc3"))

    time.sleep(1)
    output = test_corpus.search("It is sunny")
    # print("OUTPUT IS : ")
    # print(output)
    assert "sunshine" in output[1][1]
    assert "weather" in output[0][1]


def test_delete_all_content(ctx):
    namespace_id = uuid.uuid4()
    corpus_id = uuid.uuid4()
    corpus_info = CorpusInfo("test_delete_all_content", namespace_id, corpus_id, CorpusType.CONVERSATION)
    test_corpus = basic_corpus.BasicCorpus(corpus_info, ctx.corpus_metadata, ctx.corpus_doc, ctx.corpus_vec)

    text1 = "The sun is high. California sunshine is great. "
    text2 = "I picked up my phone and then dropped it again. I cant seem to get a good grip on things these days. It persists into my everyday tasks"
    text3 = "The weather is great today, but I worry that tomorrow it won't be. My umbrella is in the repair shop."

    assert test_corpus.store_and_index(text1, Citation("www.docsource1", "SSSdoc1", "", "doc1"))
    assert test_corpus.store_and_index(text2, Citation("were.docsource2", "SSSdoc2", "", "doc2"))
    assert test_corpus.store_and_index(text3, Citation("docsource3.ai", "SSSdoc3", "", "doc3"))

    time.sleep(1)
    output = test_corpus.search("It is sunny")
    assert "sunshine" in output[1][1]

    test_corpus.delete_all_content()
    time.sleep(1)
    output = test_corpus.search("It is sunny")
    assert output == []
