import numpy as np
import uuid
import time
from memas.interface.storage_driver import DocumentEntity
from memas.storage_driver.corpus_vector_store import CorpusVectorStore
from memas.storage_driver import corpus_vector_store, corpus_doc_store, corpus_doc_metadata
from memas.corpus import basic_corpus
from memas.interface.corpus import Citation

corpus_name = "test corpus1"
test_corpus = basic_corpus.BasicCorpus(uuid.uuid4(), corpus_name)


def test_save_then_search_one_corpus(es_client):
    text1 = "The sun is high. California sunshine is great. "
    text2 = "I picked up my phone and then dropped it again. I cant seem to get a good grip on things these days. It persists into my everyday tasks"
    text3 = "The weather is great today, but I worry that tomorrow it won't be. My umbrella is in the repair shop."

    assert test_corpus.store_and_index(text1, "doc1", Citation("www.docsource1", "SSSdoc1", corpus_name, ""))
    assert test_corpus.store_and_index(text2, "doc2", Citation("were.docsource2", "SSSdoc2", corpus_name, ""))
    assert test_corpus.store_and_index(text3, "doc3", Citation("docsource3.ai", "SSSdoc3", corpus_name, ""))

    time.sleep(1)
    output = test_corpus.search("It is sunny")
    print("OUTPUT IS : ")
    print(output)
    assert "sunshine" in output[0][0]
    assert "weather" in output[1][0]
    assert False
